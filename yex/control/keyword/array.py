r"""
Array controls.

These controls implement blocks of registers. For example, ``\dimen``
is a block of 256 numbered registers, all of which represent a length.
"""
import collections
import yex
import string
import logging
from yex.control import Unexpandable, Register, Array
from yex.value import *
from yex.box import Box as ybBox
from yex.font import Font

logger = logging.getLogger('yex.general')

class Count(Array):
    our_type = Number

    def __setitem__(self, index, v):

        if isinstance(v, int):
            v = Number(v)

        try:
            if v.value<-2**31 or v.value>2**31:
                raise ValueError(
                        f"Assignment is out of range: {v.value}")
        except (TypeError, AttributeError):
            # This isn't the right type for us, but the superclass
            # can deal with that.
            pass

        super().__setitem__(index, v)

class Dimen(Array):
    our_type = Dimen

class Skip(Array):
    our_type = Glue

class Muskip(Array):
    our_type = Muglue

class Toks(Array):
    our_type = Tokenlist

class Box(Array):
    our_type = ybBox

    destroy_on_read = True

    def get_directly(self, index):

        exists = index in self.contents

        result = super().get_directly(index)

        if exists:
            if self.destroy_on_read:
                logger.debug("destroying contents of box %d",
                        index)
                del self.contents[index]
            else:
                logger.debug("not destroying contents of box %d",
                        index)

        return result

    def _value_for_repr(self, index):
        index = self._check_index(index)

        if index in self.contents:
            return yex.box.Box.list_to_symbols_for_repr(
                    self.contents[index])
        else:
            return '(empty)'

    def set_from_tokens(self, index, tokens):
        index = self._check_index(index)

        tokens.eat_optional_char('=')

        logger.debug("%s%s: looking for new value",
                self, index)

        box = tokens.next(level='querying')

        logger.debug("%s%s:   -- found %s",
                self, index, box)

        if 'value' in dir(box):
            box = box.value
            logger.debug("%s%s:   -- dereferenced: %s",
                    self, index, box)

        if isinstance(box, yex.box.Box):
            self.__setitem__(index, box)
        else:
            raise yex.exception.ExpectedBoxError(
                    problem=box,
                    )

    @classmethod
    def _check_index(cls, index):
        if index<0 or index>255:
            raise KeyError(index)
        return index

class Copy(Box):
    destroy_on_read = False

    def __init__(self, doc):
        self.doc = doc
        self.contents = doc[r'\box'].contents

class Catcode(Array):
    our_type = int

    max_value = 15

    @classmethod
    def _default_contents(cls):
        result = {
                "\\":  0, # Escape character
                '{':   1, # Beginning of group
                '}':   2, # End of group
                '$':   3, # Math shift
                '&':   4, # Alignment tab
                '\n':  5, # End of line
                '\r':  5,
                '#':   6, # Parameter
                '^':   7, # Superscript
                '_':   8, # Subscript
                '\0':  9, # Ignored character
                ' ':  10, # Space
                # 11: Letter
                # 12: Other
                '~':  13, # Active character
                '%':  14, # Comment character
                chr(127): 15, # Invalid character,
                }

        for pair in [
                ('a', 'z'),
                ('A', 'Z'),
            ]:

            for c in range(ord(pair[0]), ord(pair[1])+1):
                result[chr(c)] = 11 # Letter

        result = dict([(ord(f), v) for f,v in result.items()])

        return collections.defaultdict(
                _twelve, # Other
                result)

    def _empty_register(self):
        return 0

    def __setitem__(self, index, value):

        value = int(value)

        if value<0 or value>self.max_value:
            raise ValueError(
                    f"Assignment is out of range: {value}")
        super().__setitem__(index, value)

    @classmethod
    def _check_index(cls, index):
        if isinstance(index, str):
            return ord(index)
        else:
            return int(index)

    def _get_a_value(self, tokens):
        return Number.from_tokens(tokens)

    def _value_for_repr(self, index):
        index = self._check_index(index)
        value = self.contents[index]

        try:
            category = yex.parse.Token.by_category[value].__name__.lower()
        except KeyError:
            category = '???'

        return f'{value} ({category})'

class Mathcode(Catcode):
    max_value = 32768

    @classmethod
    def _check_index(cls, index):
        return index

    @classmethod
    def _default_contents(cls):
        return MathcodeDefaultDict()

class Uccode(Array):
    our_type = int

    @classmethod
    def _default_contents(cls):
        return collections.defaultdict(
                _zero,
                dict([
                    (ord(c), ord(cls.default_mapping(c)))
                    for c in string.ascii_letters]))

    @classmethod
    def default_mapping(cls, c):
        return c.upper()

    @classmethod
    def _check_index(cls, index):
        if isinstance(index, int):
            return index
        elif isinstance(index, str):
            return ord(index)
        else:
            raise IndexError(index)

    @classmethod
    def _check_value(cls, value):
        if isinstance(value, int):
            return value
        elif isinstance(value, str):
            return ord(value)
        else:
            raise ValueError(value)

class Lccode(Uccode):

    @classmethod
    def default_mapping(cls, c):
        return c.lower()

class Sfcode(Array):
    our_type = Number

    @classmethod
    def _default_contents(cls):
        return collections.defaultdict(
                _one_thousand,
                dict([
                    (c, 999)
                    for c in string.ascii_uppercase]))

    @classmethod
    def _check_index(cls, index):
        if isinstance(index, int):
            return chr(index)
        else:
            return index

class Delcode(Array):
    our_type = Number

    @classmethod
    def _default_contents(cls):
        return collections.defaultdict(
                _minus_one,
                {'.': 0},
                )

    @classmethod
    def _check_index(cls, index):
        if isinstance(index, int):
            return chr(index)
        else:
            return index

class Textfont(Array):
    our_type = Font

    @classmethod
    def _check_index(cls, index):
        if index<0 or index>15:
            raise KeyError(index)
        else:
            return index

    def _get_a_value(self, tokens):
        result = tokens.next(level="querying")
        return result

    def _check_value(self, value):
        if isinstance(value, yex.control.keyword.FontSetter):
            value = value.value
        return value

    def _empty_register(self):
        raise KeyError()

class Scriptfont(Textfont): pass
class Scriptscriptfont(Textfont): pass

def _minus_one():
    return -1
def _zero():
    return 0
def _twelve():
    return 12
def _one_thousand():
    return 1000

class MathcodeDefaultDict(dict):
    def __missing__(self, c):
        # See p154 of the TeXbook.
        if chr(c) in string.digits:
            return c+0x7000
        elif chr(c) in string.ascii_letters:
            return c+0x7100
        else:
            return c
