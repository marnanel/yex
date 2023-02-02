import yex.value
from yex.box.box import *
from yex.box.gismo import *
import yex.parse
import logging
import yex

logger = logging.getLogger('yex.general')

VERY_LOOSE = 0
LOOSE = 1
DECENT = 2
TIGHT = 3

class HVBox(Box):
    """
    A Box which contains some number of Gismos, in some order.

    This is an abstract class; its descendants HBox and VBox are
    the ones you want to actually use.

    Attributes:

        badness (int): a measure of how well this box can fit on a line.
            This gets set by fit_to(), which receives the length of line
            we're looking for. Before fit_to() is called, it's 0.
        decency (int): a measure of how loose the spacing is.
            This gets set by fit_to(). Before fit_to() is called, it's None.
            One of VERY_LOOSE, LOOSE, DECENT, or TIGHT.
            These are integer constants, and they can be compared.

        VERY_LOOSE: for lines with far too much space between the words
        LOOSE: for lines with too much space between the words
        DECENT: for lines with sensible amounts of space between the words
        TIGHT: for lines with too little space between the words
    """

    def __init__(self, *args,
            to=None, spread=None,
            glue_set = None,
            height = 0, width = 0, depth = 0,
            ):

        if args:
            raise yex.exception.YexInternalError(
                    "Create boxes using from_contents(), not directly."
                    )

        super().__init__(
                height = height,
                width = width,
                depth = depth,
                )

        self.to = require_dimen(to)
        self.spread = require_dimen(spread)
        self.shifted_by = yex.value.Dimen(0)

        self.badness = 0 # positively angelic 😇
        self.decency = DECENT

        self.glue_set = glue_set

    def _length_in_dominant_direction(self):
        """
        Width for a horizontal box, or full height for a vertical box.
        """

        lengths = [
            self.dominant_accessor(n)
            for n in
            self.contents
            ]

        result = sum(lengths, start=yex.value.Dimen())

        logger.debug(
                '%s: lengths in dominant direction (sum=%s): %s',
                self, result, lengths)

        return result

    def _length_in_non_dominant_direction(self, c_accessor,
            shifting_polarity):
        """
        Full height for a horizontal box, or width for a vertical box.

        Args:
            c_accessor: function which takes a Gismo and returns
                the length of that Gismo.

                This is needed because the full height of any box
                is composed of a height and a depth. So, when we're working
                out the full height of a VBox, we have to look both up
                for each of its children.

                It isn't needed with _length_in_dominant_direction(),
                because the full width of an HBox is visible with only
                one accessor.

            shifting_polarity (int): -1 if `child.shifted_by` decreases
                the result, 0 if it makes no difference, and 1 if it increases.
        """

        lengths = [
            c_accessor(n) + n.shifted_by*shifting_polarity
            for n in
            self.contents
            ]

        result = max(lengths, default=yex.value.Dimen())

        logger.debug(
                '%s: lengths in non-dominant direction (max=%s): %s',
                self, result, lengths)

        return result

    def _adjust_dimens_for_item(self, item):
        raise NotImplementedError()

    def _showbox_one_line(self,
            name=None):

        name = name or self.__class__.__name__.lower()

        result = r'\%s(%s+%s)x%s' % (
                name,
                self.height.__repr__(show_unit=False),
                self.depth.__repr__(show_unit=False),
                self.width.__repr__(show_unit=False),
                )

        if self.glue_set is not None:
            result += ', glue set '
            result += self.glue_set

        if self.shifted_by.value:
            result += ', shifted '
            result += self.shifted_by.__repr__(show_unit=False)

        return result

    def __repr__(self):
        result = super().__repr__()[:-1]

        if int(self.spread)!=0:
            result += f';spread={self.spread}'

        if int(self.to)!=0:
            result += f';to={self.to}'

        result += ']'
        return result

    def _repr(self):
        result = ''

        if int(self.spread)!=0:
            result += f':spread={self.spread}'

        if int(self.to)!=0:
            result += f':to={self.to}'

        result += super()._repr()
        return result

    def __getstate__(self):

        import yex.box

        current_font = None

        # The palaver with checking the font is because every character
        # has a font associated with it, but if we put a "font" value on
        # each one, the output would be unreadable. So we note what
        # the first one was, plus any changes.

        result = {}

        contents = []
        for item in self.contents:

            if hasattr(item, 'font'):
                font = item.font

                if 'font' not in result:
                    current_font = font
                    result['font'] = font.name

                elif current_font!=font:
                    contents.append(
                            {'font': font.name},
                            )

                    current_font = font

            if isinstance(item, yex.box.WordBox):

                for c in item.contents:
                    if isinstance(c, CharBox):
                        if not contents or not isinstance(contents[-1], str):
                            contents.append('')

                        contents[-1] += c.ch
                    else:
                        contents.append(
                                c.__getstate__())
            else:
                contents.append(item.__getstate__())

        result[self.__class__.__name__.lower()] = contents

        return result

    single_symbol='?'

    @property
    def symbol(self):
        result = '[%s%s]' % (
                self.single_symbol,
                self.list_to_symbols_for_repr(self.contents),
                )

        return result

    @classmethod
    def from_contents(cls,
            contents,
            *args, **kwargs,
            ):
        result = cls(*args, **kwargs)

        result.contents = contents
        for item in contents:
            result._adjust_dimens_for_item(item)

        logger.debug(
                '%s: created with contents=%s and width=%s (%ssp)',
                result, result.contents, result.width, result.width.value)

        return result

class HBox(HVBox):
    """
    A box whose contents are arranged horizontally.

    For example, a line of type.

    Text in HBoxes can be wordwrapped at points called Breakpoints.
    HBoxes insert Breakpoints as they go along.
    """

    inside_mode = 'Restricted_Horizontal'
    dominant_accessor = lambda self, c: c.width

    def _offset_fn(self, c):
        return c.width

    def _adjust_dimens_for_item(self, item):
        self.width += item.width
        self.height = max(
                self.height,
                item.height - item.shifted_by,
                )
        self.depth = max(
                self.depth,
                item.depth + item.shifted_by,
                )

    @property
    def demerits(self):
        """
        The demerits of this HBox, considered as a line of type.

        The algorithm is at the foot of p97 of the TeXBook.

        Raises:
            ValueError: if this box does not end with a Breakpoint.
        """
        raise NotImplementedError("Going away!")

        try:
            final = self.contents[-1]
        except IndexError:
            raise ValueError("An empty list has no demerits")

        if not isinstance(final, Breakpoint):
            raise ValueError(
                    "Only lists ending with Breakpoints have demerits")

        b = self.badness
        p = final.penalty

        linepenalty = 10
        # TODO when we have access to the doc, look this up-- see issue #50

        result = (linepenalty + b)**2

        if p>=0:
            result += p**2
        elif p>-10000:
            result -= p**2

        logger.debug("%s: demerits==%s (b==%s, p==%s, l==%s)",
                self, result, b, p, linepenalty)

        return result

    single_symbol = '▸'

class VBox(HVBox):
    """
    A box whose contents are arranged vertically.

    For example, a paragraph.
    """

    inside_mode = 'Internal_Vertical'
    dominant_accessor = lambda self, c: c.height+c.depth

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _offset_fn(self, c):
        return yex.value.Dimen(), c.height+c.depth

    def _adjust_dimens_for_item(self, item):
        self.width = max(
                self.width,
                item.width,
                )

        self.height += self.depth # i.e. of the previous item
        self.height += item.height

        self.depth = item.depth

    def insert(self, where, thing):

        if isinstance(thing, VBox):
            if where is not None:
                raise yex.exception.InternalError(
                        "HBox.insert() merging VBoxes is only supported if "
                        "where is None (i.e. at the end); "
                        "if you don't like this, please fix it")

            self.contents.extend(thing.contents)
            self._adjust_dimens_for_item(thing)

            logger.debug(
                '%s: extended our contents by %s; now: %s',
                self, thing, self.contents)

        else:

            super().insert(where, thing)

    single_symbol = '⯆'

class VtopBox(VBox):
    pass

class Page(VBox):
    """
    A page in the document.

    Just an ordinary VBox, really. We keep it in a subclass to make debugging
    easier.
    """

    def _showbox_one_line(self):
        # pretend to be an ordinary vbox
        return super()._showbox_one_line(name='vbox')

    def __repr__(self):
        result = super().__repr__()[:-1]
        result += ' (page)]'
        return result
