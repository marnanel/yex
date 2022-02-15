import copy
import datetime
import mex.value
import mex.box
import mex.parameter
import mex.control
import mex.register
import mex.mode
import re
import logging

macros_logger = logging.getLogger('mex.macros')

KEYWORD_WITH_INDEX = re.compile('([a-z]+)([0-9]+)')

class State:

    def __init__(self):

        self.lineno = 1
        self.created_at = datetime.datetime.now()

        controls = mex.control.ControlsTable()
        controls |= mex.macro.handlers()
        controls |= mex.parameter.handlers(self)

        self.values = [
                {
                    'count': mex.register.CountsTable(),
                    'dimen': mex.register.DimensTable(),
                    'skip': mex.register.SkipsTable(),
                    'muskip': mex.register.MuskipsTable(),
                    'toks': mex.register.ToksTable(),
                    'box': mex.register.BoxTable(),
                    'hyphenation': mex.register.HyphenationTable(),
                    'catcode': mex.register.CatcodesTable(),
                    'mathcode': mex.register.MathcodesTable(),
                    'uccode': mex.register.UccodesTable(),
                    'lccode': mex.register.LccodesTable(),
                    'sfcode': mex.register.SfcodesTable(),
                    'delcode': mex.register.DelcodesTable(),
                    'controls': controls,
                    'fonts': {},
                    }
            ]

        self.next_assignment_is_global = False

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

        if field in self.values[-1]['controls']:
            self.values[-1]['controls'][field] = value
            macros_logger.info(f"  -- \\{field}:={value}")
            return

        raise KeyError(field)

    def set(self, field, value,
            block = None):

        if self.next_assignment_is_global:
            macros_logger.debug("global: %s = %s, block==%s",
                    field, value, block)

            for i in range(len(self.values)):
                self._setitem_for_grouping(
                        field, value,
                        block,
                        grouping = i)

            self.next_assignment_is_global = False
        else:
            macros_logger.debug("%s = %s, block==%s",
                    field, value, block)

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
            macros_logger.debug("  -- incomplete register name")

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
        self.next_assignment_is_global = False

    def __getattr__(self, block):
        return self.values[-1][block]

    def __len__(self):
        return len(self.values)

    @property
    def mode(self):
        return self.values[-1]['controls']['_mode'].mode
