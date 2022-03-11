import os
import mex.value
import mex.mode
import mex.exception
import mex.font
from mex.control import C_Expandable
import logging

commands_logger = logging.getLogger('mex.commands')

# Parameters; see pp269-271 of the TeXbook,
# and lines 275ff of plain.tex.

NUMBER_PARAMETERS = [
        "pretolerance",
        "tolerance",
        "hbadness",
        "vbadness",
        "linepenalty",
        "hyphenpenalty",
        "exhyphenpenalty",
        "binoppenalty",
        "relpenalty",
        "clubpenalty",
        "widowpenalty",
        "displaywidowpenalty",
        "brokenpenalty",
        "predisplaypenalty",
        "postdisplaypenalty",
        "interlinepenalty",
        "floatingpenalty",
        "outputpenalty",
        "doublehyphendemerits",
        "finalhyphendemerits",
        "adjdemerits",
        "looseness",
        "pausing",
        "holdinginserts",
        "language",
        "uchyph",
        "lefthyphenmin",
        "righthyphenmin",
        "globaldefs",
        "defaulthyphenchar",
        "defaultskewchar",
        "escapechar",
        "endlinechar",
        "newlinechar",
        "maxdeadcycles",
        "hangafter",
        "fam",
        "mag",
        "delimiterfactor",
        "showboxbreadth",
        "showboxdepth",
        "errorcontextlines",

        # and internal integers

        "spacefactor",
        "prevgraf",
        "deadcycles",
        "insertpenalties",
        "lastpenalty",
        "badness",
        ]

DIMEN_PARAMETERS = [
        "hfuzz",
        "vfuzz",
        "overfullrule",
        "emergencystretch",
        "hsize",
        "vsize",
        "maxdepth",
        "splitmaxdepth",
        "boxmaxdepth",
        "lineskiplimit",
        "delimitershortfall",
        "nulldelimiterspace",
        "scriptspace",
        "mathsurround",
        "predisplaysize",
        "displaywidth",
        "displayindent",
        "parindent",
        "hangindent",
        "hoffset",
        "voffset",

        # and internal dimens

        "lastkern",
        "pagetotal",
        "pagegoal",
        "pagestretch",
        "pagefilstretch",
        "pagefillstretch",
        "pagefilllstretch",
        "pageshrink",
        "pagedepth",

        "prevdepth",
        ]

GLUE_PARAMETERS = [
        "baselineskip",
        "lineskip",
        "parskip",
        "abovedisplayskip",
        "abovedisplayshortskip",
        "belowdisplayskip",
        "belowdisplayshortskip",
        "leftskip",
        "rightskip",
        "topskip",
        "splittopskip",
        "tabskip",
        "spaceskip",
        "xspaceskip",
        "parfillskip",

        # and internal glues

        "lastskip",
        ]

MUGLUE_PARAMETERS = [
        "thinmuskip",
        "medmuskip",
        "thickmuskip",
        ]

TOKENLIST_PARAMETERS = [
        "output",
        "everypar",
        "everymath",
        "everydisplay",
        "everyhbox",
        "everyvbox",
        "everyjob",
        "everycr",
        "errhelp",
        ]

# Anything not listed here has the default initial value,
# which for number params is zero.
# These should be the INITEX values; plain.tex
# can set them to other things as it pleases.

PARAMETER_INITIAL_VALUES = {
        "tolerance": 10000,
        "escapechar": 92,
        "endlinechar": 13,
        "hangafter": 1,
        "mag": 1000,
        "spacefactor": 1000,
        }

class Parameter(C_Expandable):
    our_type = None

    def __init__(self, value=None):
        if value is None:
            self._value = self.our_type()
        else:
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

    def get_the(self, name, tokens):
        if isinstance(self.value, str):
            return self.value
        else:
            return repr(self.value)

    def __call__(self, name, tokens):
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
        self.basename = 'cmr10'
        self.font = None
        self.fonts_dir = ''

    @property
    def value(self):
        if self.font is None:
            self.font = mex.font.Font(
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
        for f in t.names:
            if f in PARAMETER_INITIAL_VALUES:
                result[f] = t(PARAMETER_INITIAL_VALUES[f])
            else:
                result[f] = t()

    ################

    now = state.created_at
    for f,v in {
            "time": now.hour*60 + now.minute,
            "day": now.day,
            "month": now.month,
            "year": now.year,
            }.items():
        result[f] = NumberParameter(v)

    ################

    g = list(globals().items())

    result |= dict([
        (name.lower(), value(state)) for
        (name, value) in g
        if value.__class__==type and
        issubclass(value, MagicParameter)
        ])

    result |= mex.log.handlers(state)

    return result
