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


NUMBER_PARAMETERS = {
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

        # and internal integers

        "spacefactor": 1000,
        "prevgraf": 0,
        "deadcycles": 0,
        "insertpenalties": 0,
        "lastpenalty": 0,
        }

DIMEN_PARAMETERS = {
        "hfuzz": mex.value.Dimen(),
        "vfuzz": mex.value.Dimen(),
        "overfullrule": mex.value.Dimen(),
        "emergencystretch": mex.value.Dimen(),
        "hsize": mex.value.Dimen(),
        "vsize": mex.value.Dimen(),
        "maxdepth": mex.value.Dimen(),
        "splitmaxdepth": mex.value.Dimen(),
        "boxmaxdepth": mex.value.Dimen(),
        "lineskiplimit": mex.value.Dimen(),
        "delimitershortfall": mex.value.Dimen(),
        "nulldelimiterspace": mex.value.Dimen(),
        "scriptspace": mex.value.Dimen(),
        "mathsurround": mex.value.Dimen(),
        "predisplaysize": mex.value.Dimen(),
        "displaywidth": mex.value.Dimen(),
        "displayindent": mex.value.Dimen(),
        "parindent": mex.value.Dimen(),
        "hangindent": mex.value.Dimen(),
        "hoffset": mex.value.Dimen(),
        "voffset": mex.value.Dimen(),

        # and internal dimens

        "lastkern": mex.value.Dimen(),

        }

GLUE_PARAMETERS = {
        "baselineskip": mex.value.Glue(),
        "lineskip": mex.value.Glue(),
        "parskip": mex.value.Glue(),
        "abovedisplayskip": mex.value.Glue(),
        "abovedisplayshortskip": mex.value.Glue(),
        "belowdisplayskip": mex.value.Glue(),
        "belowdisplayshortskip": mex.value.Glue(),
        "leftskip": mex.value.Glue(),
        "rightskip": mex.value.Glue(),
        "topskip": mex.value.Glue(),
        "splittopskip": mex.value.Glue(),
        "tabskip": mex.value.Glue(),
        "spaceskip": mex.value.Glue(),
        "xspaceskip": mex.value.Glue(),
        "parfillskip": mex.value.Glue(),

        # and internal glues

        "lastskip": mex.value.Glue(),
        }

MUGLUE_PARAMETERS = {
        "thinmuskip": mex.value.Muglue(),
        "medmuskip": mex.value.Muglue(),
        "thickmuskip": mex.value.Muglue(),
        }

TOKENLIST_PARAMETERS = {
        "output": mex.value.Tokenlist(),
        "everypar": mex.value.Tokenlist(),
        "everymath": mex.value.Tokenlist(),
        "everydisplay": mex.value.Tokenlist(),
        "everyhbox": mex.value.Tokenlist(),
        "everyvbox": mex.value.Tokenlist(),
        "everyjob": mex.value.Tokenlist(),
        "everycr": mex.value.Tokenlist(),
        "errhelp": mex.value.Tokenlist(),
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

    def set_from(self, tokens):
        tokens.eat_optional_equals()
        v = self.our_type(tokens)
        commands_logger.debug("Setting %s=%s",
                self, v)
        self.value = v

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

    def __int__(self):
        return int(self._value)

class NumberParameter(Parameter):
    our_type = int
    names = NUMBER_PARAMETERS

    def set_from(self, tokens):
        tokens.eat_optional_equals()
        number = mex.value.Number(tokens)
        self.value = number.value
        commands_logger.debug("Setting %s=%s",
                self, self.value)

class DimenParameter(Parameter):
    our_type = mex.value.Dimen
    names = DIMEN_PARAMETERS

class GlueParameter(Parameter):
    our_type = mex.value.Glue
    names = GLUE_PARAMETERS

class MuglueParameter(GlueParameter):
    our_type = mex.value.Muglue
    names = MUGLUE_PARAMETERS

class TokenlistParameter(Parameter):
    our_type = mex.value.Tokenlist
    names = TOKENLIST_PARAMETERS

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

    for t in [
            NumberParameter,
            DimenParameter,
            GlueParameter,
            MuglueParameter,
            TokenlistParameter,
            ]:
        for f,v in t.names.items():
            result[f] = t(v)

    now = state.created_at
    for f,v in {
            "time": now.hour*60 + now.minute,
            "day": now.day,
            "month": now.month,
            "year": now.year,
            }.items():
        result[f] = NumberParameter(v)

    g = list(globals().items())

    result |= dict([
        (name.lower(), value(state)) for
        (name, value) in g
        if value.__class__==type and
        issubclass(value, MagicParameter)
        ])

    result |= mex.log.handlers(state)

    return result
