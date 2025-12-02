import yex
import yex.logging
from typing import Union, List, Self

logger = yex.logging.getLogger('box')

class Gismo:
    r"""
    Something which can appear on a page, usually inside a box.

    The spelling is as given in the TeXbook. In modern times,
    this is spelt "[gizmo](https://en.wiktionary.org/wiki/gizmo)".

    All gismos have a width, a height, and a depth.
    Their x-dimension is their width.
    Their y-dimension is their height plus their depth.
    Any of these may be negative.

    They are measured from a point on the page called their
    "reference point", which is not stored in the gismo instance
    itself. From this point, height is measured upwards,
    depth downwards, and width to the right.

    ![Diagram of height, depth, and width](../_static/character-in-box.svg)

    Attributes:
        height (Union[Dimen,None]): the height of the gismo;
            the vertical length of the gismo consists of this and "depth".

        depth (Union[Dimen,None]):  the depth of the gismo;
            the vertical length of the gismo consists of this and "height".

        width (Union[Dimen,None]):  the horizontal length of the gismo.

        shifted_by (Dimen): how far to shift this Gismo downwards on the page.
            Almost always zero. Can be negative, which shifts the Gismo
            upwards instead.

        discardable (bool): if this is True, the wordwrap algorithm will
            drop the Gismo at the beginning of a new line. If it's False,
            it won't.

        showbox (List[str]): what `\showbox` should display for this gismo.

        kind (str): what kind of Gismo we are-- our class name, lowercased.

        symbol (str): one character for the kind of gismo this is,
            used for debug logging.
            For word boxes, this is the first character of the word.
            Otherwise, it can be any Unicode symbol you like.
    """

    shifted_by = yex.value.Dimen()
    discardable = False
    ch = ''

    def __init__(self,
                 height:Union['yex.value.Dimen',None] = None,
                 width:Union['yex.value.Dimen',None] = None,
                 depth:Union['yex.value.Dimen',None] = None,
                 ):
        self._height = require_dimen(height)
        self._depth = require_dimen(depth)
        self._width = require_dimen(width)
        self.contents = []
        self.parent = None

    def _get_dimension(self, name:str) -> 'yex.value.Dimen':
        return getattr(self, f'_{name}')
    def _set_dimension(self, name:str, v:'yex.value.Dimen') -> None:
        if not isinstance(v, yex.value.Dimen) and v is not None:
            raise yex.exception.ExpectedDimenOrNoneError(problem=v)
        setattr(self, f'_{name}', v)

    @property
    def height(self) -> 'yex.value.Dimen':
        return self._get_dimension('height')
    @height.setter
    def height(self, v:'yex.value.Dimen') -> None:
        self._set_dimension('height', v)

    @property
    def width(self) -> 'yex.value.Dimen':
        return self._get_dimension('width')
    @width.setter
    def width(self, v:'yex.value.Dimen') -> None:
        self._set_dimension('width', v)

    @property
    def depth(self) -> 'yex.value.Dimen':
        return self._get_dimension('depth')
    @depth.setter
    def depth(self, v:'yex.value.Dimen') -> None:
        self._set_dimension('depth', v)

    def showbox(self) -> List[str]:
        return [f'\\{self.kind}']

    def is_void(self) -> bool:
        return False

    @property
    def kind(self) -> str:
        return self.__class__.__name__.lower()

    def insert(self, where: Union[int, None], thing: Self) -> None:
        """
        Inserts a gismo into our contents. After insertion,
        `thing` will be a member of our contents, and
        `thing.parent` will be equal to us.

        Other than the gismo to be inserted, the order of
        our contents will remain the same.

        Args:
            where: the index of `thing` after the insertion.
                If this is None, `thing` will be inserted
                at the end.
            thing: whatever it is you want to insert.

        Raises:
            ValueError: if this class of gismo doesn't allow
                insertion
            TypeError: if `thing` is not a gismo
        """
        raise ValueError("I don't allow insertion.")

    def extract(self) -> Self:
        """
        Removes us from our parent gismo. After this call,
        we will not be a member of the former parent's
        contents list, and `self.parent` will be None.

        If we didn't have a parent, this is a no-op.

        Returns:
            ourselves
        """
        return self

    def __repr__(self):
        return f'[{self.kind}]'

    def __getstate__(self):

        result = {
                self.kind: list(self.contents),
                }

        return result

    @property
    def symbol(self):
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
