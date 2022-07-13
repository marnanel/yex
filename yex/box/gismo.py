import yex.value
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

    Attributes:
        doc: the current document
        on_box_render: a callable; we will run it with no parameters,
            at most once, if and when this Whatsit is rendered.
    """

    discardable = False

    def __init__(self,
            on_box_render,
            ):
        super().__init__()
        self.on_box_render = on_box_render

    def __call__(self):
        logger.debug("%s: we're being rendered, so run %s",
                self, self.on_box_render)
        result = self.on_box_render()
        logger.debug("%s: call to %s finished",
                self, self.on_box_render)
        logger.debug("%s:   -- it returned: %s",
                self, result)
        return result

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

class Leader(Gismo):
    """
    Leaders, although at present this only wraps Glue.
    """

    discardable = True

    def __init__(self,
            *args,
            glue=None,
            vertical=False,
            **kwargs,
            ):
        """
        Constructor.

        Args:
            glue (`Glue`): glue for the new Leader to wrap.
               If this is None, we construct a new Glue using **kwargs
               and wrap that, instead.

            vertical (`bool`): True if this Leader is vertical,
                False if it's horizontal.
        """

        if glue is not None:
            self.glue = glue
        else:
            self.glue = yex.value.Glue(**kwargs)

        self.vertical = vertical

        for name in [
                'space', 'stretch', 'shrink',
                ]:
            setattr(self, name, getattr(self.glue, name))

    @classmethod
    def from_another(cls, another):
        result = cls.__new__(cls)
        result.vertical = another.vertical

        if another.glue is None:
            result.glue = None
        else:
            result.glue = yex.value.Glue.from_another(another.glue)

        return result

    @property
    def contents(self):
        return []

    @property
    def width(self):
        if self.vertical:
            return yex.value.Dimen(0)
        else:
            return self.glue.space

    @property
    def height(self):
        if self.vertical:
            return self.glue.space
        else:
            return yex.value.Dimen(0)

    @property
    def depth(self):
        return yex.value.Dimen(0)

    def __repr__(self):
        return repr(self.glue)

    def showbox(self):
        return [r'\glue '+self.glue.__repr__(show_unit=False)]

    def __eq__(self, other):
        try:
            return self.vertical==other.vertical and \
                    self.glue==other.glue
        except AttributeError:
            return False

    def __getstate__(self):
        """
        The value, in terms of simple types.

        Since Leaders occur all over the place in the final output,
        where they're almost always finite with no stretch or shrink,
        we represent that as a special case: just the integer size
        of the space.

        Otherwise, this is the same as the __getstate__() of the glue.
        """

        result = self.glue.__getstate__()

        if len(result)==1:
            result = result[0]

        return result

    @property
    def symbol(self):
        return '︙'

class Kern(Gismo):
    """
    An adjustment of horizontal spacing.

    For example, a kern would appear between the capital letters "A" and "V".
    """

    discardable = True

    def __init__(self, width):
        super().__init__(
                width = width,
                )

    def __repr__(self):
        return f'[kern: {self.width}]'

    def showbox(self):
        return [r'\kern %.5g' % (
            float(self.width),)]

    def __getstate__(self):
        return {
                'kern': self.width.value,
                }

    @property
    def symbol(self):
        return '∿'

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
