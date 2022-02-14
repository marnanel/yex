import mex.value
import mex.exception

# Parameters; see pp269-271 of the TeXbook,
# and lines 275ff of plain.tex.
# These should be the INITEX values; plain.tex
# can set them to other things as it pleases.

INTEGER_PARAMETERS = {
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
        }

# XXX Params for other types

dummy = {
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
        }

class Parameter:

    our_type = None

    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, n):
        self._value = n

    def set_from(self, tokens):
        raise ValueError("superclass")

    def __repr__(self):
        return '['+repr(self._value)+']'

    def __deepcopy__(self, memo):
        result = self.__class__(self._value)
        return result

class IntegerParameter(Parameter):
    our_type = int

    def set_from(self, tokens):
        number = mex.value.Number(tokens)
        self._value = number.value

# Classes whose name begins "Magic" are returned by handlers()
# (and thus entered into the controls dict by State)
# with the "Magic" stripped and the name lowercased.
# If they begin "Magic_" they won't be accessible by the user,
# because their name in the controls dict will being with an underscore.

class Magic_currentfont:

    def __init__(self, state):
        self.state = state
        self.basename = 'cmr10'
        self.font = None

    @property
    def value(self):

        import mex.font

        if self.font is None:
            self.font = mex.font.Metrics(
                    filename=f'other/{self.basename}.tfm',
                    )
        return self.font

    @value.setter
    def value(self, n):
        self.basename = n

    def __deepcopy__(self, memo):
        result = self.__class__(self.state)
        result.basename = self.basename
        result.font = self.font
        return result

class MagicInputlineno:

    def __init__(self, state):
        self.state = state

    @property
    def value(self):
        return self.state.lineno

    @value.setter
    def value(self, n):
        raise mex.exceptions.MacroError(
                "Can't set value of inputlineno",
                self.state)

    def __deepcopy__(self, memo):
        result = self.__class__(self.state)
        return result

def handlers(state):

    import mex.log

    result = {}
    for f,v in INTEGER_PARAMETERS.items():
        result[f] = IntegerParameter(v)

    now = state.created_at
    for f,v in {
            "time": now.hour*60 + now.minute,
            "day": now.day,
            "month": now.month,
            "year": now.year,
            }.items():
        result[f] = IntegerParameter(v)

    result |= dict([
        (name[5:].lower(), value(state)) for
        (name, value) in globals().items()
        if value.__class__==type and
        name.startswith('Magic')
        ])

    result |= mex.log.handlers(state)

    return result
