import collections
import yex.value
import yex.exception
import yex.control
import string
import logging

logger = logging.getLogger('yex.general')

class Register:
    """
    A simple wrapper so we can pass out references to
    entries in a RegisterTable, and have them update
    the original values.
    """

    is_outer = False

    def __init__(self, parent, index):
        self.parent = parent
        self.index = index

    @property
    def value(self):
        return self.parent.get_directly(self.index)

    @value.setter
    def value(self, n):
        self.parent[self.index] = n

    def __repr__(self):
        return f"[{self.identifier}]"

    @property
    def identifier(self):
        return fr"\{self.parent.name()}{self.index}"

    def set_from_tokens(self, tokens):
        """
        Sets the value from the tokeniser "tokens".
        """
        try:
            self.parent.set_from_tokens(self.index, tokens)
        except TypeError as te:
            raise yex.exception.ParseError(
                    te.args[0])

    def __call__(self, tokens):
        """
        Sets the value from the tokeniser "tokens".

        Mimics a control.C_Control object.
        """
        self.set_from_tokens(tokens)

    def get_the(self, tokens):
        """
        Returns the list of tokens to use when we're representing
        this register with \\the (see p212ff of the TeXbook).

        It is acceptable to return a string; it will be
        converted to a list of the appropriate character tokens.
        """
        return str(self.value)

    @property
    def our_type(self):
        return self.parent.our_type

    def __iadd__(self, other):
        self.value += other
        return self

    def __imul__(self, other):
        self.value *= other
        return self

    def __itruediv__(self, other):
        self.value /= other
        return self

    def __int__(self):
        # this may not work in all cases, but that's for the
        # parent object to figure out.
        return int(self.value)

    def __eq__(self, other):
        if isinstance(other, Register):
            if self.parent!=other.parent:
                raise TypeError(
                        "Can't compare Registers of different types: "
                        f"{self.parent.__class__.__name__} versus "
                        f"{other.parent.__class__.__name__}"
                        )
            return self.value==other.value
        elif isinstance(other, self.parent.our_type):
            return self.value==other
        elif isinstance(other, str):
            return str(self.value)==other
        else:
            raise TypeError(
                    "Can't compare "
                    f"{self.parent.__class__.__name__} Registers with "
                    f"{other.__class__.__name__}."
                    )

class RegisterTable:

    our_type = None

    def __init__(self, doc, contents=None):

        self.doc = doc

        if contents is None:
            self.contents = {}
        else:
            self.contents = contents

    def get_directly(self, index):
        index = self._check_index(index)

        try:
            return self.contents[index]
        except KeyError:
            return self._empty_register()

    def __getitem__(self, index):
        index = self._check_index(index)
        return Register(
            parent = self,
            index = index,
            )

    def __setitem__(self, index, value):
        index = self._check_index(index)
        value = self._check_value(value)

        was = self.contents.get(index, None)

        if value is None:
            if index in self.contents:
                del self.contents[index]
        else:
            self.contents[index] = value

        self.doc.remember_restore(
                fr'\{self.name()}{index}', was)

    def set_from_tokens(self, index, tokens):
        logger.debug("%s: set_from_tokens begins..",
                self)
        index = self._check_index(index)

        logger.debug("%s: set_from_tokens index==%s",
                self, index)
        tokens.eat_optional_equals()

        v = self._get_a_value(tokens)

        logger.debug("%s: set_from_tokens value==%s",
                self, v)

        self.__setitem__(index, v)
        logger.debug("%s: done!",
                self)

    def _get_a_value(self, tokens):
        return self.our_type(tokens)

    def _check_index(self, index):
        if index<0 or index>255:
            raise KeyError(index)
        return index

    def _check_value(self, value):
        if value is None:
            return None
        elif isinstance(value, self.our_type):
            return value
        elif hasattr(value, 'value'):
            return value.value
        elif self.our_type==yex.value.Number and isinstance(value, int):
            return yex.value.Number(value)
        else:
            raise yex.exception.YexError(
                    f"Expected a {self.our_type.__name__}, "
                    f"but got {value} of type {value.__class__.__name__}")

    def _empty_register(self):
        return self.our_type()

    def __contains__(self, index):
        return index in self.contents

    @property
    def _type_to_parse(self):
        return self.our_type

    @classmethod
    def name(cls):
        # note: not "stable" like reliable.
        # it turns e.g. "CountsTable" into "Count".
        return cls.__name__.lower().replace('stable','')

class CountsTable(RegisterTable):

    our_type = yex.value.Number

    def _empty_register(self):
        return yex.value.Number(0)

    def __setitem__(self, index, v):

        if isinstance(v, int):
            v = yex.value.Number(v)

        try:
            if v.value<-2**31 or v.value>2**31:
                raise ValueError(
                        f"Assignment is out of range: {v.value}")
        except (TypeError, AttributeError):
            # This isn't the right type for us, but the superclass
            # can deal with that.
            pass

        super().__setitem__(index, v)

class DimensTable(RegisterTable):

    our_type = yex.value.Dimen

class SkipsTable(RegisterTable):

    our_type = yex.value.Glue

class MuskipsTable(RegisterTable):

    our_type = yex.value.Glue

class ToksTable(RegisterTable):

    our_type = yex.value.Tokenlist

    @classmethod
    def name(cls):
        return 'toks'

class BoxTable(RegisterTable):

    our_type = yex.box.Box

    def get_directly(self, index,
            no_destroy = False):

        exists = index in self

        result = super().get_directly(index)

        if exists:
            if no_destroy:
                logger.info("not destroying contents of box%d",
                        index)
            else:
                logger.info("destroying contents of box%d",
                        index)
                del self.contents[index]

        return result

    def set_from_tokens(self, index, tokens):
        index = self._check_index(index)

        tokens.eat_optional_equals()

        logger.info("%s: looking for new value",
                self)

        box = tokens.next(level='querying')

        logger.info("%s:   -- found %s",
                self, box)

        if 'value' in dir(box):
            box = box.value
            logger.info("%s:   -- dereferenced: %s",
                    self, box)

        if isinstance(box, yex.box.Box):
            self.__setitem__(index, box)
        else:
            raise yex.exception.ParseError(
                    f"not a box: {box}",
                    )

    @classmethod
    def name(cls):
        return 'box'

class CopyTable(RegisterTable):
    our_type = yex.box.Box

    def __init__(self, doc):
        self.doc = doc

    def _corresponding(self, index):
        return self.doc[f'box{index}']

    def get_directly(self, index):
        return self._corresponding(index).parent.get_directly(
                index,
                no_destroy = True,
                )

    def __setitem__(self, index, value):
        # yes, you can assign to copyNN (and not only during restores)
        self._corresponding(index).value = value

    def set_from_tokens(self, index, tokens):
        self._corresponding(index).value.set_from_tokens(index, tokens)

    def _check_index(self, index):
        if index<0 or index>255:
            raise KeyError(index)
        return index

    def _empty_register(self):
        return None

    @classmethod
    def name(cls):
        return 'copy'

class HyphenationTable(RegisterTable):

    our_type = list

class CatcodesTable(RegisterTable):

    our_type = int
    max_value = 15

    def default_code_table(self):
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

        return collections.defaultdict(
                lambda: 12, # Other
                result)

    def __init__(self, doc, contents=None):
        if contents is None:
            contents = self.default_code_table()
        super().__init__(doc, contents)

    def _empty_register(self):
        return 0

    def __setitem__(self, index, value):

        value = int(value)

        if value<0 or value>self.max_value:
            raise ValueError(
                    f"Assignment is out of range: {value}")
        super().__setitem__(index, value)

    def _check_index(self, index):
        if isinstance(index, int):
            return chr(index)
        else:
            return index

    def _get_a_value(self, tokens):
        return yex.value.Number(tokens)

class MathcodesTable(CatcodesTable):
    max_value = 32768

    def _check_index(self, index):
        return index

    def default_code_table(self):

        class MathcodeDefaultDict(dict):

            def __missing__(self, c):
                # See p154 of the TeXbook.
                if chr(c) in string.digits:
                    return c+0x7000
                elif chr(c) in string.ascii_letters:
                    return c+0x7100
                else:
                    return c

        return MathcodeDefaultDict()

class UccodesTable(RegisterTable):

    our_type = yex.value.Number

    def __init__(self, doc, contents=None):
        if contents is None:
            contents = collections.defaultdict(
                lambda: 0,
                dict([
                    (c, ord(self.mapping(c)))
                    for c in string.ascii_letters]))

        super().__init__(doc, contents)

    def mapping(self, c):
        return c.upper()

    def _check_index(self, index):
        if isinstance(index, int):
            return chr(index)
        else:
            return index

class LccodesTable(UccodesTable):
    def mapping(self, c):
        return c.lower()

class SfcodesTable(RegisterTable):

    our_type = yex.value.Number

    def __init__(self, doc, contents=None):
        if contents is None:
            contents = collections.defaultdict(
                lambda: 1000,
                dict([
                    (c, 999)
                    for c in string.ascii_uppercase]))

        super().__init__(doc, contents)

    def _check_index(self, index):
        if isinstance(index, int):
            return chr(index)
        else:
            return index

class DelcodesTable(RegisterTable):

    our_type = yex.value.Number

    def __init__(self, doc, contents=None):
        if contents is None:
            contents = collections.defaultdict(
                lambda: -1,
                {'.': 0},
                )

        super().__init__(doc, contents)

    def _check_index(self, index):
        if isinstance(index, int):
            return chr(index)
        else:
            return index

class TextfontsTable(RegisterTable):

    our_type = yex.font.Font

    def _check_index(self, index):
        if index<0 or index>15:
            raise KeyError(index)
        else:
            return index

    def _get_a_value(self, tokens):
        result = tokens.next(level="querying")
        return result

    def _check_value(self, value):
        if isinstance(value, yex.control.C_FontSetter):
            value = value.value
        return value

class ScriptfontsTable(TextfontsTable): pass
class ScriptscriptfontsTable(TextfontsTable): pass

def handlers(doc):

    g = list(globals().items())

    result = dict([
        (value.name(), value(doc)) for
        (name, value) in g
        if value.__class__==type and
        value!=RegisterTable and
        issubclass(value, RegisterTable)
        ])

    return result
