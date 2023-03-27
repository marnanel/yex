import yex.value
from yex.box.gismo import *
import yex.parse
import logging
import yex
import copy

logger = logging.getLogger('yex.general')

class Box(Gismo):
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

    Attributes:
        height (Dimen): the height of the box; the vertical length of the
            box consists of this and "depth".
        depth (Dimen):  the depth of the box; the vertical length of the
            box consists of this and "height".
        width (Dimen):  the horizontal length of the box.
        contents (list): the Gismos inside the box
        inside_mode (str): the name of the mode which governs the contents
            of this box. In the superclass, this is None.
    """

    inside_mode = None
    discardable = False

    def __init__(self, height=None, width=None, depth=None):
        self.height = require_dimen(height)
        self.width = require_dimen(width)
        self.depth = require_dimen(depth)

        self.contents = []

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

        for ours, theirs in zip(self.contents, other.contents):
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
        result = r'[\%s;%04x;%s]' % (
                self.__class__.__name__.lower(),
                id(self) % 0xffff,
                self.list_to_symbols_for_repr(self.contents),
                )
        return result

    def _repr(self):
        result = ''
        for i in self.contents:
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

    def __getstate__(self):
        result = {
                self.kind: list(self.contents),
                }

        for attr in ['height', 'width', 'depth']:
            value = getattr(self, attr)
            if value:
                result[attr[0]] = value.__getstate__()

        return result

    def _showbox_one_line(self):
        return '\\'+self.__class__.__name__.lower()

    def is_void(self):
        return self.contents==[]

    def __getitem__(self, n):
        if isinstance(n, slice):
            result = copy.copy(self)
            result.contents = self.contents[n]
        elif isinstance(n, int):
            result = self.contents[n]
        else:
            raise TypeError(n)

        return result

    @classmethod
    def list_to_symbols_for_repr(cls, items):
        """
        Turns a list of Boxes into the symbols for those boxes.

        Only to be used in __repr__ methods, for debugging.

        Args:
            items (list of Box): the items we want the symbols for

        Returns:
            str, the symbols for those items
        """
        def _symbol_for(thing):
            if hasattr(thing, 'symbol'):
                return thing.symbol
            else:
                return thing.__class__.__name__

        result = ''.join([
            _symbol_for(x) for x in items])

        return result

    @classmethod
    def from_tokens(cls, tokens):
        r"""
        Constructs a Box from tokens.

        If you call this method on yex.box.Box, it will read in and parse
        a box specification, of the form

            \hbox{...}

        where \hbox could be any box-defining control. We return the
        new box, which is of the type returned by the control.

        However, if the next item in "tokens" is not a token but an
        actual box, we return that box.

        If you call it on one of the subclasses, we read in and parse
        a box specification. We don't expect to deal with the opening control.
        We return the new box, which will be an instance of the
        subclass you were calling.

        Again, if the next item in "tokens" is not a token but a box
        of the appropriate class, we return that box.

        Specifications for box syntax are on p274 of the TeXbook.

        Args:
            tokens (`Tokeniser`): the tokeniser

        Returns:
            the new Box
        """

        if cls==Box:
            logger.debug('Box.from_tokens: creating new box')
            t = tokens.next(level='reading')

            if isinstance(t, cls):
                logger.debug('Box.from_tokens: returning existing box, %s',
                        t)
                return t
            elif isinstance(t,
                    (yex.parse.Control, yex.control.Control)):
                logger.debug(
                        'Box.from_tokens: the new box will be created by %s',
                        t)

                tokens.push(t)
                box = tokens.next(level='querying')

                if not isinstance(box, cls):
                    raise yex.exception.YexError(
                            "expected a box, but found %s (which is a %s)" % (
                                box, box.__class__.__name__))

                logger.debug('Box.from_tokens: returning new box: %s',
                        box)
                return box
            else:
                raise yex.exception.YexError(
                        "expected the definition of a box, but "
                        "found %s (which is a %s)" % (
                            t, t.__class__.__name__))
        else:
            # we're in a subclass, so we know what kind of box we're creating

            mode = getattr(yex.mode, cls.inside_mode)
            assert mode is not None

            t = tokens.next(level='querying')
            if isinstance(t, cls):
                logger.debug('%s.from_tokens: found a box, %s',
                        cls.__name__, t)
                return t

            tokens.push(t)

            logger.debug('%s.from_tokens: creating new box, in mode %s',
                    cls.__name__, mode)

            if tokens.optional_string('to'):
                to = yex.value.Dimen.from_tokens(tokens)
                spread = None
            elif tokens.optional_string('spread'):
                to = None
                spread = yex.value.Dimen.from_tokens(tokens)
            else:
                to = None
                spread = None

            tokens.eat_optional_spaces()

            opening_symbol = tokens.next(level='deep')
            if not isinstance(opening_symbol, yex.parse.BeginningGroup):
                logger.debug( (
                    "%s.from_tokens: group didn't begin with "
                    "the opening symbol, but with %s (which is a %s)"),
                    cls.__name__, opening_symbol, type(opening_symbol))

                raise ValueError(
                    f"The group didn't begin with the opening symbol, "
                    f"but with {opening_symbol} "
                    f"(which is a {type(opening_symbol)}."
                    )

            # okay, put it back, or Expander(bounded='single')
            # will get confused
            tokens.push(opening_symbol)

            newbox = []
            def handle(result):
                newbox.append(result)

            new_mode = mode(
                    doc = tokens.doc,
                    to = to,
                    spread = spread,
                    box_type = cls,
                    recipient = handle,
                    )

            group = tokens.doc.begin_group(flavour='only-mode')

            tokens.doc['_mode'] = new_mode

            logger.debug("%s.from_tokens: beginning creation of new box",
                    cls.__name__)

            inner_tokens = tokens.another(
                    bounded='single',
                    on_eof='exhaust',
                    level='reading',
                    )

            for t in inner_tokens:
                logger.debug("%s.from_tokens: passing %s to %s",
                        cls.__name__, t, inner_tokens.doc.mode)
                inner_tokens.doc.mode.handle(
                        item=t,
                        tokens=tokens,
                        )

            tokens.doc.end_group(
                    group = group,
                    tokens = tokens,
                    )

            if not newbox:
                raise ValueError("No box was created!")

            logger.debug("%s.from_tokens: new box created: %s",
                    cls.__name__, newbox[0])

            return newbox[0]

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
                height = yex.value.Dimen.from_another(metric.height),
                width = yex.value.Dimen.from_another(metric.width),
                depth = yex.value.Dimen.from_another(metric.depth),
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
            return [r'\%s %s (ligature %s)' % (
                self.font.identifier, self.ch,
                self.from_ligature,
                )]
        else:
            return [r'\%s %s' % (self.font.identifier, self.ch)]

    def __getstate__(self):
        return self.ch

    @property
    def symbol(self):
        return self.ch
