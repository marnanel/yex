import yex.value
from yex.box.gismo import *
import yex.parse
import logging
import wrapt
import yex

logger = logging.getLogger('yex.general')

class Box(C_Box):

    """
    A Box is a rectangle on the page. It's not necessarily visible.

    All Boxes have a width, a height, and a depth.
    Their x-dimension is their width.
    Their y-dimension is their height plus their depth.
    Any of these may be negative.

    They are measured from a point on the page called their
    "reference point", which is not stored in the Box instance
    itself. From this point, height is measured upwards,
    depth downwards, and width to the right.
    """

    def __init__(self, height=None, width=None, depth=None,
            contents=None,
            ):

        not_a_tokenstream(height)

        self.height = require_dimen(height)
        self.width = require_dimen(width)
        self.depth = require_dimen(depth)

        if contents is None:
            self._contents = []
        else:
            self._contents = contents

        # in the general case, these are two names for the same thing
        self.contents = self._contents

    def set_from_tokens(self, index, tokens):
        index = self._check_index(index)

        tokens.eat_optional_equals()

        for e in tokens.single_shot():
            box = e

        if isinstance(box, yex.box.Box):
            self.__setitem__(index, box)
        else:
            raise yex.exception.ParseError(
                    "not a box: {box}",
                    )

    def __eq__(self, other):
        return self._compare(other, depth = 0)

    def _compare(self, other, depth=0):
        debug_indent = '  '*depth
        logger.debug("%sComparing %s and %s...",
                debug_indent,
                self, other)

        if not isinstance(other, self.__class__):
            logger.debug("%s  -- types differ, %s %s so False",
                    debug_indent, other.__class__, self.__class__)
            return False

        if len(self)!=len(other):
            logger.debug("%s  -- lengths differ, so False",
                    debug_indent)
            return False

        # we compare their contents, not their _contents, so that
        # we don't compare line breaks

        for ours, theirs in zip(self._contents, other.contents):
            logger.debug("%s  -- comparing %s and %s",
                    debug_indent,
                    ours, theirs)
            if not ours._compare(theirs,
                    depth = depth+1,
                    ):
                logger.debug("%s  -- they differ, so False",
                    debug_indent,
                    )
                return False

        logger.debug("%s  -- all good, so True!",
                    debug_indent,
                    )
        return True

    def __repr__(self):
        result = r'[\%s:%04x]' % (
                self.__class__.__name__.lower(),
                id(self) % 0xffff,
                )
        return result

    def _repr(self):
        result = ''
        for i in self._contents:
            result += ':' + repr(i)

        return result

    def __len__(self):
        # length does not include line breaks
        return len(self.contents)

    def showbox(self):
        r"""
        Returns a list of lines to be displayed by \showbox.

        We keep this separate from the repr() routine on purpose.
        The formatting and the information to display are
        too different to merge them.
        """
        result = [self._showbox_one_line()]

        for c in self.contents:
            result.extend(['.'+x for x in c.showbox()])

        return result

    def _showbox_one_line(self):
        return '\\'+self.__class__.__name__.lower()

    def is_void(self):
        return self._contents==[]

    def __getitem__(self, n):
        if isinstance(n, slice):
            result = _SlicedBox(
                    wrapped=self,
                    the_slice=n,
                    )
        elif isinstance(n, int):
            result = self._contents[n]
        else:
            raise TypeError(n)

        return result

class _SlicedBox(wrapt.ObjectProxy):
    """
    A slice of a box.

    This is a proxy object.
    """

    badness = 0 # don't use the "badness" attribute of the wrapper

    def __init__(self, wrapped, the_slice):
        super(_SlicedBox, self).__init__(wrapped)
        self._self_slice = the_slice
        self.badness = 0

    @property
    def contents(self):
        result = self.__wrapped__.contents[self._self_slice]
        return result

    def fit_to(self, size,
            badness_param = None,
            ):
        logger.debug("%s: fit_to() is using the slice",
                self)

        self.badness = self._inner_fit_to(
                size = size,
                contents = self.contents,
                badness_param = badness_param,
                )

    def __repr__(self):
        return repr(self.__wrapped__)[:-1]+f';{self._self_slice}]'

    def __str__(self):
        return str(self.__wrapped__)[:-1]+f';{self._self_slice}]'

class Rule(Box):
    """
    A Rule is a box which appears black on the page.
    """
    def __str__(self):
        return fr'[\rule; {self.width}x({self.height}+{self.depth})]'

class CharBox(Box):
    """
    A Box containing single character from a font.

    Attributes:
        ch (str): the character
        font: the font
        from_ligature (str): the ligature that produced this character,
            or None if there wasn't one. Usually this is None.
            It's only used for diagnostics.
    """
    def __init__(self, font, ch):

        metric = font[ch].metrics
        super().__init__(
                height = yex.value.Dimen(metric.height, 'pt'),
                width = yex.value.Dimen(metric.width, 'pt'),
                depth = yex.value.Dimen(metric.depth, 'pt'),
                )

        self.font = font
        self.ch = ch
        self.from_ligature = None

    def __repr__(self):
        if self.from_ligature is not None:
            return f'[{self.ch} from {self.from_ligature}]'
        else:
            return f'[{self.ch}]'

    def showbox(self):
        if self.from_ligature is not None:
            return [r'%s %s (ligature %s)' % (
                self.font, self.ch,
                self.from_ligature,
                )]
        else:
            return [r'%s %s' % (self.font, self.ch)]
