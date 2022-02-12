import copy
import datetime
import mex.value
import mex.box
import mex.parameter
import mex.control
import collections
import re
import string
import logging

macros_logger = logging.getLogger('mex.macros')

KEYWORD_WITH_INDEX = re.compile('([a-z]+)([0-9]+)')

class Variable:
    """
    A simple wrapper so we can pass out references to
    entries in a VariableTable, and have them update
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
        this variable with \\the (see p212ff of the TeXbook).

        It is acceptable to return a string; it will be
        converted to a list of the appropriate character tokens.
        """
        return str(self.value)

class VariableTable:

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
            return self._empty_variable()

    def __getitem__(self, index):
        index = self._check_index(index)
        return Variable(
            parent = self,
            index = index,
            )

    def __setitem__(self, index, value):
        index = self._check_index(index)

        if isinstance(value, self.our_type):
            self.contents[index] = value
        elif isinstance(value, Variable):
            self.contents[index] = v.value
        else:
            raise TypeError(f"Needed {our_type} but received {type(v)}")

        return Variable(
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

    def _empty_variable(self):
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

class CountsTable(VariableTable):

    our_type = int

    def _empty_variable(self):
        return 0

    def _parse_value(self, tokens):
        number = mex.value.Number(tokens)
        return number.value

    def __setitem__(self, index, value):
        if value<-2**31 or value>2**31:
            raise ValueError(
                    f"Assignment is out of range: {value}")
        super().__setitem__(index, value)

class DimensTable(VariableTable):

    our_type = mex.value.Dimen

    def _parse_value(self, tokens):
        return mex.value.Dimen(tokens)

class SkipsTable(VariableTable):

    our_type = mex.box.Glue

    def _parse_value(self, tokens):
        raise ValueError("implement skipsdict")

class MuskipsTable(VariableTable):

    our_type = mex.box.Glue

    def _parse_value(self, tokens):
        raise ValueError("implement muskipsdict")

class CatcodesTable(VariableTable):

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

    def _empty_variable(self):
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

class UccodesTable(VariableTable):

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

class SfcodesTable(VariableTable):

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

class DelcodesTable(VariableTable):

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

class State:

    def __init__(self):

        self.lineno = 1
        self.created_at = datetime.datetime.now()

        controls = mex.control.ControlsTable()
        controls |= mex.macro.handlers()
        controls |= mex.parameter.handlers(self)

        self.values = [
                {
                    'count': CountsTable(),
                    'dimen': DimensTable(),
                    'skip': SkipsTable(),
                    'muskip': MuskipsTable(),
                    'catcode': CatcodesTable(),
                    'mathcode': MathcodesTable(),
                    'uccode': UccodesTable(),
                    'lccode': LccodesTable(),
                    'sfcode': SfcodesTable(),
                    'delcode': DelcodesTable(),
                    'controls': controls,
                    'fonts': {},
                    }
            ]

    def _setitem_for_grouping(self, field, value, block, grouping):

        if block is not None:
            # We've been given the block directly, so we don't
            # have to look for where to put this value.
            #
            # This also means we can add new items to the block,
            # rather than being restricted to updating existing ones.
            # This is the reason for the union operator below,
            # rather than going through __setitem__.
            self.values[grouping][block] |= {field: value}
            return

        for prefix in [
                'count',
                'dimen',
                'skip',
                'muskip',
                ]:

            if field.startswith(prefix):
                index = int(field[len(prefix):])

                if index<0 or index>255:
                    raise KeyError(field)

                self.values[grouping][prefix][index] = value

                return

        raise KeyError(field)

    def set(self, field, value,
            block = None,
            use_global = False):

        if use_global:
            for i in range(len(self.values)):
                self._setitem_for_grouping(
                        field, value,
                        block,
                        grouping = i)
        else:
            self._setitem_for_grouping(
                    field, value,
                    block,
                    grouping = -1)

    def __setitem__(self, field, value):
        self.set(field, value)

    def __getitem__(self, field,
            tokens=None):

        m = re.match(KEYWORD_WITH_INDEX, field)

        if m is not None:
            keyword, index = m.groups()
            result = self.values[-1][keyword][int(index)]
            macros_logger.info(f"  -- \\{field}=={result}")
            return result

        if field in self.values[-1]['controls']:
            result = self.values[-1]['controls'][field]
            macros_logger.info(f"  -- \\{field}=={result}")
            return result

        macros_logger.debug("%s, %s %s", field, field in self.values[-1], tokens)
        if field in self.values[-1] and tokens is not None:
            macros_logger.debug("  -- incomplete variable name")

            index = mex.value.Number(tokens).value
            macros_logger.debug("  -- index is %s", index)
            result = self.values[-1][field][index]
            macros_logger.info(f"  -- \\{field}{index}=={result}")
            return result

        raise KeyError(field)

    def get(self, field, default=None,
            tokens=None):
        try:
            return self.__getitem__(field, tokens)
        except KeyError:
            return default

    def begin_group(self):
        self.values.append(copy.deepcopy(self.values[-1]))

    def end_group(self):
        if len(self.values)<2:
            raise ValueError("More groups ended than began!")
        self.values.pop()

    def __getattr__(self, block):
        return self.values[-1][block]

    def __len__(self):
        return len(self.values)
