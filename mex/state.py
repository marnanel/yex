import copy
import datetime
import mex.value
import mex.box
import mex.parameter
import mex.control

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

class VariableTable:

    our_type = None

    def __init__(self, contents=None):

        if contents is None:
            self.contents = {}
        else:
            self.contents = contents

    def get_directly(self, index):
        self._check_index(index)

        try:
            return self.contents[index]
        except KeyError:
            return self._empty_variable()

    def __getitem__(self, index):
        self._check_index(index)
        return Variable(
            parent = self,
            index = index,
            )

    def __setitem__(self, index, value):
        self._check_index(index)

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

    def set_from(self, index, tokens):
        self._check_index(index)

        v = self._parse_value(tokens)

        self.__setitem__(index, v)

    def _check_index(self, index):
        if index<0 or index>255:
            raise KeyError(index)

    def _empty_variable(self):
        raise KeyError()

    def _parse_value(self, tokens):
        raise ValueError("superclass")

    def __deepcopy__(self, memo):
        result = self.__class__(
                contents = copy.deepcopy(
                    self.contents,
                    memo,
                    ))
        return result

class CountsTable(VariableTable):

    our_type = int

    def _empty_variable(self):
        return 0

    def _parse_value(self, tokens):
        number = mex.value.Number(tokens)
        return number.value

    def _check_new_value(self, counter_type, value):
        if counter_type == 'count':
                if value<-2**31 or value>2**31:
                    raise ValueError(
                            f"Assignment is out of range: {value}")

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

class State:

    def __init__(self):

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
                    'controls': controls,
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

    def __getitem__(self, field):

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

                return self.values[-1][prefix][index]

        if field in self.values[-1]['controls']:
            return self.values[-1]['controls'][field]

        raise KeyError(field)

    def get(self, field, default=None):
        try:
            return self.__getitem__(field)
        except KeyError:
            return default

    def set_catcode(self, char, catcode):
        self.values[-1]['charcode'][char] = catcode

    def get_catcode(self, char):
        return self.values[-1]['charcode'][char]

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

    def add_block(self, name, value):
        self.values[-1][name] = value
