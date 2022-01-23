import copy
import datetime
from mex.value import Dimen
from mex.box import Glue

class State:

    def __init__(self):

        now = datetime.datetime.now()

        self.values = [{
            'count': {},
            'dimen': {},
            'skip': {},
            'muskip': {},

            # Parameters; see pp269-271 of the TeXbook,
            # and lines 275ff of plain.tex.
            # These should be the INITEX values; plain.tex
            # can set them to other things as it pleases.

            # Integer parameters:
            "pretolerance": 0,
            "tolerance": 10000,
            "hbadness": 0,
            "vbadness": 0,
            "linepenalty": 0,
            "hyphenpenalty": 0,
            "exhyphenpenalty": 0,
            "binoppenalty": 0,
            "relpenalty": 0,
            "clubpenalty": 0,
            "widowpenalty": 0,
            "displaywidowpenalty": 0,
            "brokenpenalty": 0,
            "predisplaypenalty": 0,
            "postdisplaypenalty": 0,
            "interlinepenalty": 0,
            "floatingpenalty": 0,
            "outputpenalty": 0,
            "doublehyphendemerits": 0,
            "finalhyphendemerits": 0,
            "adjdemerits": 0,
            "looseness": 0,
            "pausing": 0,
            "holdinginserts": 0,
            "tracingonline": 0,
            "tracingmacros": 0,
            "tracingstats": 0,
            "tracingparagraphs": 0,
            "tracingpages": 0,
            "tracingoutput": 0,
            "tracinglostchars": 0,
            "tracingcommands": 0,
            "tracingrestores": 0,
            "language": 0,
            "uchyph": 0,
            "lefthyphenmin": 0,
            "righthyphenmin": 0,
            "globaldefs": 0,
            "defaulthyphenchar": 0,
            "defaultskewchar": 0,
            "escapechar": 92,
            "endlinechar": 13,
            "newlinechar": 0,
            "maxdeadcycles": 0,
            "hangafter": 1,
            "fam": 0,
            "mag": 1000,
            "delimiterfactor": 0,
            "time": now.hour*60 + now.minute,
            "day": now.day,
            "month": now.month,
            "year": now.year,
            "showboxbreadth": 0,
            "showboxdepth": 0,
            "errorcontextlines": 0,
            "hfuzz": 0,
            "vfuzz": 0,
            "overfullrule": 0,
            "emergencystretch": 0,
            "hsize": 0,
            "vsize": 0,
            "maxdepth": 0,
            "splitmaxdepth": 0,
            "boxmaxdepth": 0,
            "lineskiplimit": 0,
            "delimitershortfall": 0,
            "nulldelimiterspace": 0,
            "scriptspace": 0,
            "mathsurround": 0,
            "predisplaysize": 0,
            "displaywidth": 0,
            "displayindent": 0,
            "parindent": 0,
            "hangindent": 0,
            "hoffset": 0,
            "voffset": 0,

            # Still to add: other non-integer params

            # Token list parameters:
            "output": [],
            "everypar": [],
            "everymath": [],
            "everydisplay": [],
            "everyhbox": [],
            "everyvbox": [],
            "everyjob": [],
            "everycr": [],
            "errhelp": [],
                    }]

    def _check_counter(self, counter_type, value):
        if counter_type == 'count':
                if value<-2**31 or value>2**31:
                    raise ValueError(
                            f"Assignment is out of range: {value}")
        elif counter_type == 'dimen':
            if not isinstance(value, Dimen):
                raise ValueError("dimens must be Dimen")
        elif counter_type == 'skip':
            if not isinstance(value, Skip):
                raise ValueError("skips must be Glue")
        elif counter_type == 'muskip':
            raise ValueError("implement muskip assignment")
        else:
            raise ValueError(f"unknown counter type: {counter_type}")

    def _setitem_for_grouping(self, field, value, grouping):

        if field in self.values[grouping]:
            self.values[grouping][field] = value
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

                self._check_counter(prefix, value)

                self.values[grouping][prefix][index] = value

                return

        if field.startswith('charcode'):
            index = int(field[9:])
            self.values[grouping]['charcode'][chr(index)] = value
            return

        if ' ' in field:
            result = self.values[grouping]
            parts = field.split(' ')
            for part in parts[:-1]:
                result = result[part]
            result[parts[-1]] = value
            return

        raise KeyError(field)

    def set(self, field, value,
            use_global = False):

        if use_global:
            for i in range(len(self.values)):
                self._setitem_for_grouping(
                        field, value,
                        grouping = i)
        else:
            self._setitem_for_grouping(
                    field, value,
                    grouping = -1)

    def __setitem__(self, field, value):
        self.set(field, value)

    def _new_counter(self, counter_type):
        if counter_type == 'count':
            return 0
        elif counter_type == 'dimen':
            raise KeyError()
        elif counter_type == 'skip':
            raise KeyError()
        elif counter_type == 'muskip':
            raise KeyError()
        else:
            raise ValueError(f"unknown counter type: {counter_type}")

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

                try:
                    return self.values[-1][prefix][index]
                except KeyError:
                    result = self._new_counter(prefix)
                    self.values[-1][prefix][index] = result
                    return result

        if field in self.values[-1]:
            return self.values[-1][field]

        if field.startswith('charcode'):
            index = int(field[9:])
            return self.values[-1]['charcode'][chr(index)]

        if ' ' in field:
            try:
                result = self.values[-1]
                for part in field.split(' '):
                    result = result[part]
                return result
            except KeyError:
                raise KeyError(field)

        raise KeyError(field)

    def get(self, field, default=None):
        try:
            return self.__getitem__(field)
        except KeyError:
            return default

    def begin_group(self):
        self.values.append(copy.deepcopy(self.values[-1]))

    def end_group(self):
        self.values.pop()

    def __len__(self):
        return len(self.values)

    def __contains__(self, item):
        try:
            self.__getitem__(item)
            return True
        except KeyError:
            return False

    def add_block(self, name, value):
        self.values[-1][name] = value
