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
        return f"[{self.identifier};{self.parent._value_for_repr(self.index)}]"

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
        else:
            try:
                return type(other)(self.value)==other
            except TypeError:
                raise TypeError(
                        "Can't compare "
                        f"{self.parent.__class__.__name__} Registers with "
                        f"{other.__class__.__name__}."
                        )

    def __getstate__(self):
        return {
                'register': f'\\{self.parent.name()}{self.index}',
                }

class RegisterTable:
    r"""
    A set of registers of a particular type.

    For example, the Dimen parameters live in registers called \dimen0,
    \dimen1, and so on. All those registers are held in a subclass of
    RegisterTable.

    The Register class is a wrapper which accesses one particular item
    in our array.

    This is an abstract class.
    """

    our_type = None

    def __init__(self, doc, contents=None):

        self.doc = doc

        if contents is None:
            self.contents = self._default_contents()
        else:
            self.contents = contents

    def get_directly(self, index):
        index = self._check_index(index)

        try:
            return self.contents[index]
        except KeyError:
            return self._empty_register()

    def _value_for_repr(self, index):
        try:
            return str(self.contents[index])
        except KeyError:
            return str(self._empty_register()) + " (empty)"

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
        logger.debug("%s: set_from_tokens begins.",
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
        try:
            return self.our_type.from_tokens(tokens)
        except AttributeError:
            # XXX Remove when issue 44 is fixed. June 2022.
            return self.our_type(tokens)

    @classmethod
    def _check_index(cls, index):
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
        else:
            try:
                return self.our_type.from_serial(value)
            except ValueError as ve:
                logger.debug((
                    "%s: tried to set a member to %s, "
                    "but %s.from_serial raised %s"),
                    self, value, self.our_type, ve)

                raise yex.exception.YexError(
                        f"Expected a {self.our_type.__name__}, "
                        f"but got {value} of type {value.__class__.__name__}")

    def _empty_register(self):
        return self.our_type()

    def __contains__(self, index):
        index = self._check_index(index)
        return index in self.contents

    @classmethod
    def _default_contents(cls):
        return {}

    @property
    def _type_to_parse(self):
        return self.our_type

    @classmethod
    def name(cls):
        # note: not "stable" like reliable.
        # it turns e.g. "CountsTable" into "Count".
        return cls.__name__.lower().replace('stable','')

    def items(self):
        """
        All the items in this table. This can be used to recreate the table.

        Yields:
            a series of pairs. The first element is a string which could
                be passed to Document[...] to recreate this item.
                The second element is the value.
        """

        default = self._default_contents()

        # This design is necessary because "default" could
        # be dict or defaultdict, and the "in" test doesn't work well
        # with the latter.
        def different_from_default(f, v):
            try:
                return default[f]!=v
            except KeyError:
                return True

        def transform_index(idx):
            # Some subclasses use characters as indexes, which we must
            # represent by their codepoints.

            if isinstance(idx, str):
                return ord(idx)
            else:
                return idx

        for f,v in self.contents.items():
            if different_from_default(f, v):
                yield (
                        fr"\{self.name()}{transform_index(f)}",
                        v,
                        )

    def keys(self):
        for k,v in self.items():
            yield k

    def values(self):
        for k,v in self.items():
            yield v

    def __contains__(self, value):
        # there may be a more efficient way!
        return value in self.values()

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
            destroy = True):

        exists = index in self.contents

        result = super().get_directly(index)

        if exists:
            if destroy:
                logger.info("destroying contents of box%d",
                        index)
                del self.contents[index]
            else:
                logger.info("not destroying contents of box%d",
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
                destroy = False,
                )

    def _value_for_repr(self, index):
        return self._corresponding(index).parent._value_for_repr(
                index,
                )

    def __setitem__(self, index, value):
        # yes, you can assign to copyNN (and not only during restores)
        self._corresponding(index).value = value

    def set_from_tokens(self, index, tokens):
        self._corresponding(index).value.set_from_tokens(index, tokens)

    @classmethod
    def _check_index(cls, index):
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
            return index
        else:
            return int(index)

    def _get_a_value(self, tokens):
        return yex.value.Number.from_tokens(tokens)

    def _value_for_repr(self, index):
        index = self._check_index(index)
        value = self.contents[index]

        try:
            category = yex.parse.Token.by_category[value].meaning
        except KeyError:
            category = '???'

        return f'{value} {category}'

class MathcodesTable(CatcodesTable):
    max_value = 32768

    @classmethod
    def _check_index(cls, index):
        return index

    @classmethod
    def _default_contents(cls):
        return MathcodeDefaultDict()

class UccodesTable(RegisterTable):

    our_type = yex.value.Number

    @classmethod
    def _default_contents(cls):
        return collections.defaultdict(
                _zero,
                dict([
                    (c, ord(cls.mapping(c)))
                    for c in string.ascii_letters]))

    @classmethod
    def mapping(cls, c):
        return c.upper()

    @classmethod
    def _check_index(cls, index):
        if isinstance(index, int):
            return chr(index)
        else:
            return index

class LccodesTable(UccodesTable):
    @classmethod
    def mapping(cls, c):
        return c.lower()

class SfcodesTable(RegisterTable):

    our_type = yex.value.Number

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

class DelcodesTable(RegisterTable):

    our_type = yex.value.Number

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

class TextfontsTable(RegisterTable):

    our_type = yex.font.Font

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
