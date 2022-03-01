import os
import mex.value
import mex.mode
import mex.exception
import logging

commands_logger = logging.getLogger('mex.commands')

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

DIMEN_PARAMETERS = {
        "baselineskip": mex.value.Dimen(0),
        "lineskip": mex.value.Dimen(0),
        "parskip": mex.value.Dimen(0),
        "abovedisplayskip": mex.value.Dimen(0),
        "abovedisplayshortskip": mex.value.Dimen(0),
        "belowdisplayskip": mex.value.Dimen(0),
        "belowdisplayshortskip": mex.value.Dimen(0),
        "leftskip": mex.value.Dimen(0),
        "rightskip": mex.value.Dimen(0),
        "topskip": mex.value.Dimen(0),
        "splittopskip": mex.value.Dimen(0),
        "tabskip": mex.value.Dimen(0),
        "spaceskip": mex.value.Dimen(0),
        "xspaceskip": mex.value.Dimen(0),
        "parfillskip": mex.value.Dimen(0),
        }

GLUE_PARAMETERS = {
        "baselineskip": mex.value.Glue(None),
        "lineskip": mex.value.Glue(None),
        "parskip": mex.value.Glue(None),
        "abovedisplayskip": mex.value.Glue(None),
        "abovedisplayshortskip": mex.value.Glue(None),
        "belowdisplayskip": mex.value.Glue(None),
        "belowdisplayshortskip": mex.value.Glue(None),
        "leftskip": mex.value.Glue(None),
        "rightskip": mex.value.Glue(None),
        "topskip": mex.value.Glue(None),
        "splittopskip": mex.value.Glue(None),
        "tabskip": mex.value.Glue(None),
        "spaceskip": mex.value.Glue(None),
        "xspaceskip": mex.value.Glue(None),
        "parfillskip": mex.value.Glue(None),
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
    is_outer = False

    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, n):
        self._value = n

    def set_from(self, tokens):
        raise NotImplementedError()

    def get_the(self):
        if isinstance(self.value, str):
            return self.value
        else:
            return repr(self.value)

    def __call__(self, name, tokens):
        """
        Mimics a control.C_ControlWord object.
        """
        self.set_from(tokens)

    def __repr__(self):
        return '['+repr(self._value)+']'

class IntegerParameter(Parameter):
    our_type = int

    def set_from(self, tokens):
        tokens.eat_optional_equals()
        number = mex.value.Number(tokens)
        self.value = number.value

    def __int__(self):
        return self.value

class DimenParameter(Parameter):
    our_type = mex.value.Dimen

    def set_from(self, tokens):
        tokens.eat_optional_equals()
        dimen = mex.value.Dimen(tokens)
        self.value = dimen.value

class GlueParameter(Parameter):
    our_type = mex.value.Glue

    def set_from(self, tokens):
        tokens.eat_optional_equals()
        glue = mex.value.Glue(tokens)
        raise ValueError(glue)
        self.space = glue.space
        self.stretch = glue.stretch
        self.shrink = glue.shrink

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
        self.fonts_dir = ''

    @property
    def value(self):

        import mex.font

        if self.font is None:
            self.font = mex.font.Metrics(
                    filename=os.path.join(
                        self.fonts_dir,
                        f'{self.basename}.tfm',
                        )
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

    for f,v in DIMEN_PARAMETERS.items():
        result[f] = DimenParameter(v)

    for f,v in GLUE_PARAMETERS.items():
        result[f] = GlueParameter(v)

    now = state.created_at
    for f,v in {
            "time": now.hour*60 + now.minute,
            "day": now.day,
            "month": now.month,
            "year": now.year,
            }.items():
        result[f] = IntegerParameter(v)

    g = list(globals().items())

    result |= dict([
        (name.lower(), value(state)) for
        (name, value) in g
        if value.__class__==type and
        issubclass(value, MagicParameter)
        ])

    result |= mex.log.handlers(state)

    return result
