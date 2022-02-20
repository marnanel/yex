import mex.value
import mex.mode
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

    def get_the(self):
        return repr(self.value)

    def __call__(self, name, tokens):
        """
        Mimics a macro.Macro object.
        """
        self.set_from(tokens)

    def __repr__(self):
        return '['+repr(self._value)+']'

class IntegerParameter(Parameter):
    our_type = int

    def set_from(self, tokens):
        number = mex.value.Number(tokens)
        self.value = number.value

    def __int__(self):
        return self.value

class MagicParameter(Parameter):
    """
    Subclasses of MagicParameter are returned by handlers()
    (and thus entered into the controls dict by State)
    with the name lowercased.

    If they begin with an underscore, they won't be accessible by the user.
    """
    pass

class _Currentfont(MagicParameter):

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

    def __repr__(self):
        return self.basename

    @value.setter
    def value(self, n):
        self.basename = n

class _Mode(MagicParameter):

    mode_handlers = mex.mode.handlers()

    def __init__(self, state,
            mode=None,
            ):
        self.state = state

        if mode is None:
            self.mode = mex.mode.Vertical(
                    self.state,
                    )
        else:
            self.mode = mode

    def __repr__(self):
        return self.mode.name

    @property
    def value(self):
        return self.mode.name

    @value.setter
    def value(self, n):
        if n not in self.mode_handlers:
            raise ValueError(f"no such mode: {n}")

        self.mode = self.mode_handlers[n](
                self.state,
                )

class Inputlineno(MagicParameter):

    def __init__(self, state):
        self.state = state
        self.source = None

    @property
    def value(self):
        return int(self)

    def __int__(self):
        if self.source is None:
            return 0
        else:
            return self.source.line_number

    @value.setter
    def value(self, n):
        raise ValueError(
                "Can't set value of inputlineno")

    def __repr__(self):
        return str(int(self))

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
        (name.lower(), value(state)) for
        (name, value) in globals().items()
        if value.__class__==type and
        issubclass(value, MagicParameter)
        ])

    result |= mex.log.handlers(state)

    return result
