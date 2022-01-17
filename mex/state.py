import copy

class State:

    def __init__(self):
        self.values = [{
            'count': [0] * 256,
            'dimen': [0] * 256,
            'skip': [0] * 256,
            'muskip': [0] * 256,

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
            # XXX time / day / month / year
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
        }]

    def __setitem__(self, field, value,
            use_global = False):

        if use_global:
            values_number = 0
        else:
            values_number = -1

        if field in self.values[values_number]:
            self.values[values_number][field] = value
            return

        for prefix in [
                'count',
                'dimen',
                'skip',
                'muskip',
                ]:

            if field.startswith(prefix):
                index = int(field[len(prefix):])

                if value<-2**31 or value>2**31:
                    raise ValueError(
                            f"Assignment to {field} is out of range: "+\
                                    "{value}")

                self.values[values_number][prefix][index] = value

                return

        if field.startswith('charcode'):
            index = int(field[9:])
            self.values[-1]['charcode'][chr(index)] = value
            return

        if ' ' in field:
            result = self.values[-1]
            parts = field.split(' ')
            for part in parts[:-1]:
                result = result[part]
            result[parts[-1]] = value
            return

        raise KeyError(f"Unknown field: {field}")

    def __getitem__(self, field,
            use_global = False):

        if use_global:
            values_number = 0
        else:
            values_number = -1

        if field in self.values[values_number]:
            return self.values[values_number][field]

        for prefix in [
                'count',
                'dimen',
                'skip',
                'muskip',
                ]:

            if field.startswith(prefix):
                index = int(field[len(prefix):])

                return self.values[values_number][prefix][index]

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
                return None

        return None

    def begin_group(self):
        self.values.append(copy.deepcopy(self.values[-1]))

    def end_group(self):
        self.values.pop()

    def add_state(self, name, value):
        self.values[-1][name] = value
