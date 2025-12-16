import yex
import yex.logging
import copy
from typing import Union, List, Self, Any

logger = yex.logging.getLogger('box')

class Gismo:
    r"""
    Something which can appear on a page. It might be a
    [box](yex.box.Box.md).

    The spelling is as given in the TeXbook. In modern times,
    this is spelt "[gizmo](https://en.wiktionary.org/wiki/gizmo)".

    Some kinds of gismo can contain other gismos. The gismo
    which contains us is known as our parent. A gismo can also
    have no parent.

    All gismos have a width, a height, and a depth.
    Their x-dimension is their width.
    Their y-dimension is their height plus their depth.
    Any of these may be negative.

    They are measured from a point on the page called their
    "reference point", which is not stored in the gismo instance
    itself. From this point, height is measured upwards,
    depth downwards, and width to the right.

    ![Diagram of height, depth, and width](../_static/character-in-box.svg)

    If you set any of these dimensions to `None`, then its value
    will be inherited from our parent. If we have no parent,
    the value will be `Dimen(0.0)`.

    For a list of kinds of Gismo, see [`Box`](yex.box.Box.md).

    Attributes:
        height (Dimen): the height of the gismo;
            the vertical length of the gismo consists of this and "depth".

        depth (Dimen):  the depth of the gismo;
            the vertical length of the gismo consists of this and "height".

        width (Dimen):  the horizontal length of the gismo.

        shifted_by (Dimen): how far to shift this Gismo downwards on the page.
            Almost always zero. Can be negative, which shifts the Gismo
            upwards instead.

        discardable (bool): if this is True, the wordwrap algorithm will
            drop the Gismo at the beginning of a new line. If it's False,
            it won't.

        showbox (List[str]): what `\showbox` should display for this gismo.

        kind (str): what kind of gismo we are-- our class name, lowercased.

        symbol (str): one character for the kind of gismo this is,
            used for debug logging.
            For word boxes, this is the first character of the word.
            Otherwise, it can be any Unicode symbol you like.

        contents (List[Gismo]): what gismos are inside us. In subclasses
            which can't contain other gismos, this is always
            the empty list. Read-only.

        parent (Union[Gismo, None]): the gismo we're inside,
            or None if we're not inside another gismo.
    """

    shifted_by = yex.value.Dimen()
    discardable = False
    ch = ''

    # A note about symbols:
    #   "symbol" is the property which returns a box's symbol.
    #     In the supertype, it returns the value of "_symbol".
    #   If you override "symbol", please set "_symbol_doc" to
    #   a brief string explaining what the generated symbol is.
    #   (But HVBox and its descendants have a different system.)
    _symbol = '☐'

    def __init__(self,
                 height:Union['yex.value.Dimen',None] = None,
                 width:Union['yex.value.Dimen',None] = None,
                 depth:Union['yex.value.Dimen',None] = None,
                 ):
        self._height = self._require_dimen(height)
        self._depth = self._require_dimen(depth)
        self._width = self._require_dimen(width)
        self._contents = []
        self.parent = None

    def _get_dimension(self, name:str) -> 'yex.value.Dimen':
        result = getattr(self, f'_{name}')

        if result is None:
            # inherit
            if self.parent is None:
                return yex.value.Dimen()
            return self.parent._get_dimension(name)

        return result

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

    @property
    def contents(self) -> List[Self]:
        return self._contents

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
        return self._symbol

    @classmethod
    def _require_dimen(cls,
                       d:Any,
                       allow_none:bool=True,
                       ) -> Union[yex.value.Dimen, None]:
        """
        Casts d to a Dimen and returns it.

        People send us all sorts of weird numeric types, and
        we need to make sure they're Dimens before we start
        doing any maths with them.

        As a special case, if d is None and allow_none is True,
        we return None.
        """
        if isinstance(d, yex.value.Dimen):
            return d
        elif d is None:
            if allow_none:
                return None
            return yex.value.Dimen(0)
        elif isinstance(d, (int, float)):
            return yex.value.Dimen(d, 'pt')
        else:
            return yex.value.Dimen(d)

    def __getitem__(self, n: Union[slice, int]) -> Self:
        if isinstance(n, slice):
            result = copy.copy(self)
            result._contents = self._contents[n]
        elif isinstance(n, int):
            result = self._contents[n]
        else:
            raise TypeError(n)

        return result

    def __len__(self) -> int:
        return len(self._contents)

    def __iter__(self):
        return self._contents.__iter__()

class DiscretionaryBreak(Gismo):
    r"""
    A pair of strings that appear before and after a break,
    along with another string that appears if there isn't a break.

    For example,
    ```
    tra\discretionary{f-}{fi}{ffi}c
    ```

    If this occurs at the end of a line, it's equivalent to
    ```
    ... traf-
    fic ...
    ```

    Otherwise it's equivalent to
    ```
    traffic
    ```
    This gives you control over the ligature that's produced.

    Created with the [`\discretionary`](yex.keyword.Discretionary.md)
    keyword.

    TeXbook:
        p95
    """

    discardable = False

    _symbol = '⍼'

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
    _symbol = '♡'

    def __call__(self):
        logger.debug("%s: we're being rendered", self)

        result = self.render()

        logger.debug("%s: returning %s", self, result)

        return result

    def render(self):
        return NotImplementedError()

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
    _symbol = '¤'

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

class MathSwitch(Gismo):
    """
    Turns math mode on or off.
    """

    _symbol_doc = 'Σ for turning on\n ς for turning off'

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
    _symbol = '⦚'

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
