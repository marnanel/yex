import collections
import mex.value
import string
import logging
import copy

macros_logger = logging.getLogger('mex.macros')

class Register:
    """
    A simple wrapper so we can pass out references to
    entries in a RegisterTable, and have them update
    the original values.
    """
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
        return f"[\\{self.parent.name}{self.index}==" +\
                repr(self.value)+"]"

    def set_from_tokens(self, tokens):
        self.parent.set_from_tokens(self.index, tokens)

    def __call__(self, name, tokens):
        """
        Mimics a macro.Macro object.
        """
        self.parent.set_from_tokens(self.index, tokens)

    def get_the(self):
        """
        Returns the list of tokens to use when we're representing
        this register with \\the (see p212ff of the TeXbook).

        It is acceptable to return a string; it will be
        converted to a list of the appropriate character tokens.
        """
        return str(self.value)

class RegisterTable:

    our_type = None

    def __init__(self, contents=None):

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

        if isinstance(value, self.our_type):
            self.contents[index] = value
        elif isinstance(value, Register):
            self.contents[index] = v.value
        else:
            raise TypeError(f"Needed {our_type} but received {type(v)}")

        return Register(
                parent = self,
                index = index,
                )

    def set_from_tokens(self, index, tokens):
        index = self._check_index(index)

        tokens.eat_optional_equals()

        v = self._parse_value(tokens)

        self.__setitem__(index, v)

    def _check_index(self, index):
        if index<0 or index>255:
            raise KeyError(index)
        return index

    def _empty_register(self):
        return 0

    def _parse_value(self, tokens):
        raise ValueError("superclass")

    def __deepcopy__(self, memo):
        result = self.__class__(
                contents = copy.deepcopy(
                    self.contents,
                    memo,
                    ))
        return result

    @property
    def name(self):
        return self.__class__.__name__.lower().replace('stable','')

class CountsTable(RegisterTable):

    our_type = int

    def _empty_register(self):
        return 0

    def _parse_value(self, tokens):
        number = mex.value.Number(tokens)
        return number.value

    def __setitem__(self, index, value):
        if value<-2**31 or value>2**31:
            raise ValueError(
                    f"Assignment is out of range: {value}")
        super().__setitem__(index, value)

class DimensTable(RegisterTable):

    our_type = mex.value.Dimen

    def _parse_value(self, tokens):
        return mex.value.Dimen(tokens)

class SkipsTable(RegisterTable):

    our_type = mex.box.Glue

    def _parse_value(self, tokens):
        raise ValueError("implement skipsdict")

class MuskipsTable(RegisterTable):

    our_type = mex.box.Glue

    def _parse_value(self, tokens):
        raise ValueError("implement muskipsdict")

class ToksTable(RegisterTable):

    our_type = []

    def _parse_value(self, tokens):
        raise ValueError("implement toks")

class BoxTable(RegisterTable):

    our_type = mex.box.Box

    def _parse_value(self, tokens):
        raise ValueError("implement box")

class HyphenationTable(RegisterTable):

    our_type = []

    def _parse_value(self, tokens):
        raise ValueError("implement hyphenation")

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

    def __init__(self, contents=None):
        if contents is None:
            contents = self.default_code_table()
        super().__init__(contents)

    def _empty_register(self):
        return 0

    def _parse_value(self, tokens):
        number = mex.value.Number(tokens)
        return number.value

    def __setitem__(self, index, value):
        if value<0 or value>self.max_value:
            raise ValueError(
                    f"Assignment is out of range: {value}")
        super().__setitem__(index, value)

    def _check_index(self, index):
        if isinstance(index, int):
            return chr(index)
        else:
            return index

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

    our_type = int

    def __init__(self, contents=None):
        if contents is None:
            contents = collections.defaultdict(
                lambda: 0,
                dict([
                    (c, self.mapping(c))
                    for c in string.ascii_letters]))

        super().__init__(contents)

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

    our_type = int

    def __init__(self, contents=None):
        if contents is None:
            contents = collections.defaultdict(
                lambda: 1000,
                dict([
                    (c, 999)
                    for c in string.ascii_uppercase]))

        super().__init__(contents)

    def _check_index(self, index):
        if isinstance(index, int):
            return chr(index)
        else:
            return index

    def _parse_value(self, tokens):
        number = mex.value.Number(tokens)
        return number.value

class DelcodesTable(RegisterTable):

    our_type = int

    def __init__(self, contents=None):
        if contents is None:
            contents = collections.defaultdict(
                lambda: -1,
                {'.': 0},
                )

        super().__init__(contents)

    def _check_index(self, index):
        if isinstance(index, int):
            return chr(index)
        else:
            return index

    def _parse_value(self, tokens):
        number = mex.value.Number(tokens)
        return number.value


