import yex.value
import logging

logger = logging.getLogger('yex.commands')

class Gismo:

    shifted_by = yex.value.Dimen()

    def __init__(self, height=None, depth=None, width=None):
        not_a_tokenstream(height)

        self.height = require_dimen(height)
        self.depth = require_dimen(depth)
        self.width = require_dimen(width)
        self.contents = []

    def showbox(self):
        r"""
        Returns a list of strings which should be displayed by \showbox
        for this gismo.
        """
        return ['\\'+self.__class__.__name__.lower()]

    def __repr__(self):
        return '['+self.__class__.__name__.lower()+']'

class DiscretionaryBreak(Gismo):

    discardable = False

    def __init__(self,
            prebreak,
            postbreak,
            nobreak,
            ):
        super().__init__()
        self.prebreak = prebreak
        self.postbreak = postbreak
        self.nobreak = nobreak

    def __repr__(self):
        return (
                f'[discretionary break: pre={self.prebreak} '
                f'post={self.postbreak} / no={self.nobreak}]'
                )

class Whatsit(Gismo):

    discardable = False
    height = depth = width = 0

    def __init__(self,
            on_box_render,
            ):
        self.on_box_render = on_box_render

    def __call__(self):
        logger.debug("%s: we're being rendered, so run %s",
                self, self.on_box_render)
        self.on_box_render()
        logger.debug("%s: call to %s finished",
                self, self.on_box_render)

class VerticalMaterial(Gismo):

    discardable = False

    def __repr__(self):
        return f'[Vertical material]'

class C_Box(Gismo):
    """
    Superclass of all Boxes.
    """
    discardable = False

class Leader(Gismo):
    """
    Leaders, although at present this only wraps Glue.
    """

    discardable = True

    PASSTHROUGH_FIELDS = ['width', 'space', 'stretch', 'shrink']

    def __init__(self, space=None, stretch=None, shrink=None,
            stretch_infinity=0, shrink_infinity=0):
        self.size = yex.value.Glue(
                space = require_dimen(space),
                stretch = require_dimen(stretch),
                shrink = require_dimen(shrink),
                stretch_infinity = stretch_infinity,
                shrink_infinity = shrink_infinity,
                )
        self.height = yex.value.Dimen(0)
        self.depth = yex.value.Dimen(0)
        self.contents = []

    def __getattr__(self, f):
        if f in self.PASSTHROUGH_FIELDS:
            result = getattr(self.size, f)
            return result
        else:
            raise KeyError(f)

    def __setattr__(self, f, v):
        if f in self.PASSTHROUGH_FIELDS:
            setattr(self.size, f, v)
        else:
            object.__setattr__(self, f, v)

    def __repr__(self):
        return repr(self.size)

class Kern(Gismo):

    discardable = True

    def __init__(self, width):
        super().__init__(
                width = width,
                )

    def __repr__(self):
        return f'[kern: {self.width.value}]'

    def showbox(self):
        return [r'\kern %.5g' % (
            float(self.width),)]

class Penalty(Gismo):

    discardable = True

    def __init__(self, demerits):
        super().__init__()
        self.demerits = demerits

    def __repr__(self):
        return f'[penalty: {self.demerits}]'

class MathSwitch(Gismo):

    discardable = True

    def __init__(self, which):
        super().__init__()
        self.which = which

    def __repr__(self):
        if self.which:
            return '[math on]'
        else:
            return '[math off]'

def require_dimen(d):
    """
    Casts d to a Dimen and returns it.

    People send us all sorts of weird numeric types, and
    we need to make sure they're Dimens before we start
    doing any maths with them.
    """
    if isinstance(d, yex.value.Dimen):
        return d
    elif d is None:
        return yex.value.Dimen()
    elif isinstance(d, (int, float)):
        return yex.value.Dimen(d, 'pt')
    else:
        return yex.value.Dimen(d)

def not_a_tokenstream(nat):
    r"""
    If nat is a Tokenstream, does nothing.
    Otherwise, raises YexError.

    Many classes can be initialised with a Tokenstream as
    their first argument. This doesn't work for boxes:
    they must be constructed using a control.
    For example,

        2pt

    is a valid Dimen, but

        {hello}

    is not a valid Box; you must write something like

        \hbox{hello}

    to construct one. So we have this helper function
    which checks the first argument of box constructors,
    in case anyone tries it (which they sometimes do).
    """
    if isinstance(nat, yex.parse.Tokenstream):
        raise yex.exception.YexError(
                "internal error: boxes can't be constructed "
                "from Tokenstreams"
                )
