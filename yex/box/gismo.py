import yex
import logging

logger = logging.getLogger('yex.general')

class Gismo:
    """
    Something which can appear on a page, usually inside a box.

    The spelling is as given in the TeXbook. In modern times,
    this is spelt "gizmo".

    Attributes:
        shifted_by (Dimen): how far to shift this Gismo downwards on the page.
            Almost always zero. Can be negative, which shifts the Gismo
            upwards instead.

        discardable (int): if this is True, the wordwrap algorithm will
            drop the Gismo at the beginning of a new line. If it's False,
            it won't.
    """

    shifted_by = yex.value.Dimen()
    discardable = False
    ch = ''

    def __init__(self, height=None, depth=None, width=None):
        self.height = require_dimen(height)
        self.depth = require_dimen(depth)
        self.width = require_dimen(width)
        self.contents = []

    def showbox(self):
        r"""
        Returns a list of strings which should be displayed by \showbox
        for this gismo.
        """
        return [f'\\{self.kind}']

    def is_void(self):
        return False

    @property
    def kind(self):
        """
        The kind of Gismo this is.

        Returns:
            the class name, lowercased.
        """
        return self.__class__.__name__.lower()

    def __repr__(self):
        return f'[{self.kind}]'

    def __getstate__(self):

        result = {
                self.kind: list(self.contents),
                }

        return result

    @property
    def symbol(self):
        """
        One character for the kind of gismo this is. Used for debug logging.

        For word boxes, this is the first character of the word.
        Otherwise, it can be any Unicode symbol you like.
        """
        return '☐'

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
                f'[discretionary break: pre={self.prebreak}; '
                f'post={self.postbreak}; no={self.nobreak}]'
                )

class Whatsit(Gismo):
    """
    A Gismo which runs some code at the moment it's rendered.

    The code runs when the Whatsit is output. Bear in mind that it might
    never be output.

    Again, blame Knuth for the name.
    """

    discardable = False

    def __call__(self):
        logger.debug("%s: we're being rendered", self)

        result = self.render()

        logger.debug("%s: returning %s", self, result)

        return result

    def render(self):
        return NotImplementedError()

    @property
    def symbol(self):
        return '♡'

class VerticalMaterial(Gismo):

    discardable = False

    def __repr__(self):
        return f'[Vertical material]'

class C_Box(Gismo):
    """
    Superclass of all Boxes.
    """
    discardable = False

class Penalty(Gismo):
    """
    The cost of breaking the line at this place.

    When we divide a paragraph into lines, some places are better to
    break at than others. Usually we work these out automatically,
    but this instructs the algorithm specifically.

    Attributes:
        demerits (int): the cost of breaking at this place.
    """

    discardable = True

    def __init__(self, demerits):
        super().__init__()
        self.demerits = demerits

    def __repr__(self):
        return f'[penalty: {self.demerits}]'

    def showbox(self):
        return [fr"\penalty {self.demerits}"]

    def __getstate__(self):
        return {
                'penalty': self.demerits,
                }

    @property
    def symbol(self):
        return '¤'

class MathSwitch(Gismo):
    """
    Turns math mode on or off.
    """

    discardable = True

    def __init__(self, which):
        super().__init__()
        self.which = which

    def __repr__(self):
        if self.which:
            return '[math on]'
        else:
            return '[math off]'

    @property
    def symbol(self):
        if self.which:
            return 'Σ'
        else:
            return 'ς'

class Breakpoint(Gismo):
    """
    A point at which the words in an HBox could wrap to the next line.

    This is not a Gismo in TeX, but it's included as one here for convenience.
    Chapter 14 of the TeXbook explains the algorithm.

    Attributes:
        penalty (int): the cost of breaking at this breakpoint.
        number (int): the number used to identify this breakpoint in logs.
            It may be None.
    """

    discardable = False

    def __init__(self, penalty=0):

        super().__init__()
        self.penalty = penalty
        self.number = None
        self.via = None
        self.total_demerits = None
        self.hbox = None
        self.line_number = 0

    def __repr__(self):
        result = '[bp'

        if self.number is not None:
            result += f':{self.number}'

        if self.penalty:
            result += f':p={self.penalty}'

        if self.via:
            result += f':via={self.via.number}'

        if self.total_demerits:
            result += f':t={self.total_demerits}'

        result += ']'

        return result

    def showbox(self):
        return []

    @property
    def symbol(self):
        return '⦚'

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
    elif str(d)=='inherit':
        return str(d)
    elif isinstance(d, (int, float)):
        return yex.value.Dimen(d, 'pt')
    else:
        return yex.value.Dimen(d)
