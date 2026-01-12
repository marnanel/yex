import yex.value
from yex.box.gismo import *
from yex.value import Dimen
import yex.parse
import yex.logging
import yex
from typing import Self, List, Union

logger = yex.logging.getLogger('box')

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

    ![Diagram of height, depth, and width](../_static/character-in-box.svg)


    Attributes:
        height (Union[Dimen,None]): the height of the box;
            the vertical length of the box consists of this and "depth".
        depth (Union[Dimen,None]):  the depth of the box;
            the vertical length of the box consists of this and "height".
        width (Union[Dimen,None]):  the horizontal length of the box.
        contents (List[Gismo]): the Gismos inside the box
        inside_mode (Union[str, None]): the name of the mode
            which governs the contents of this box.
            In the superclass, this is None.

    # Kinds of box (and similar things)

    Unlike all other packages in yex, Box is not the supertype of *all*
    the other classes in `yex.box`: the supertype of all the classes listed
    below is [Gismo](yex.box.Gismo.md). But we named the package after
    Box, because it's far more understandable that way.

    The symbols in the "Symbol" column are what's shown in the `repr()`
    of the object.

    [Generated table]
    """

    inside_mode = None
    discardable = False

    def __eq__(self, other: Self) -> bool:
        return self._compare(other, depth = 0)

    def _compare(self, other: Self, depth=0) -> bool:
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

    def __repr__(self) -> str:
        result = r'[\%s;%04x;%s]' % (
                self.__class__.__name__.lower(),
                id(self) % 0xffff,
                self.list_to_symbols_for_repr(self._contents),
                )
        return result

    def _repr(self) -> str:
        result = ''
        for i in self._contents:
            result += ':' + repr(i)

        return result

    def __len__(self) -> int:
        """
        The number of items in this box, not including line breaks.
        """
        return len(self._contents)

    def showbox(self) -> List[str]:
        r"""
        Returns a list of lines to be displayed by `\showbox`.

        We keep this separate from the `repr()` routine on purpose.
        The formatting and the information to display are
        too different to merge them.
        """
        result = [self._showbox_one_line()]

        for c in self._contents:
            result.extend(['.'+x for x in c.showbox()])

        return result

    def __getstate__(self) -> dict:
        result = {
                self.kind: list(self._contents),
                }

        for attr in ['height', 'width', 'depth']:
            value = getattr(self, attr)
            if value:
                result[attr[0]] = value.__getstate__()

        return result

    def _showbox_one_line(self) -> str:
        return '\\'+self.__class__.__name__.lower()

    def is_void(self) -> bool:
        return self._contents==[]

    def insert(self, where, thing):
        raise ValueError("This kind of box does not allow insertion.")

    @classmethod
    def list_to_symbols_for_repr(cls,
                                 items: List['yex.box.Gismo'],
                                 ) -> str:
        """
        Turns a list of Boxes into the symbols for those boxes.

        Only to be used in `__repr__` methods, for debugging.

        Args:
            items: the items we want the symbols for
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
    def from_parser(cls, parser: 'yex.parse.Parser') -> Self:
        r"""
        Constructs a Box from tokens. The behaviour depends on whether
        you call this on `Box` itself or one of its subclasses.

        Specifications for box syntax are on p274 of the TeXbook.

        # If you call this method on `yex.box.Box`

        It will read in and parse a box specification, of the form

            \hbox{...}

        where `\hbox` could be any box-defining control. We return the
        new box, which is of the type returned by the control.

        However, if the next item in "parser" is not a token but an
        actual box, we return that box.

        # If you call it on one of the subclasses

        The behaviour is just the same, except that
        we don't deal with the opening control. (You must have
        known it already in order to find the subclass.)
        The new box will be an instance of the subclass you were calling.

        Args:
            parser: the parser
        """

        if cls==Box:
            logger.debug('Box.from_parser: creating new box')
            t = parser.next(level='reading')

            if isinstance(t, cls):
                logger.debug('Box.from_parser: returning existing box, %s',
                        t)
                return t
            elif isinstance(t,
                    (yex.parse.ControlName, yex.control.Control)):
                logger.debug(
                        'Box.from_parser: the new box will be created by %s',
                        t)

                parser.push(t)
                box = parser.next(level='querying')

                if not isinstance(box, cls):
                    raise yex.exception.ExpectedBoxError(
                            problem = box,
                            )

                logger.debug('Box.from_parser: returning new box: %s',
                        box)
                return box
            else:
                raise yex.exception.ExpectedBoxError(
                        problem = t,
                        )
        else:
            # we're in a subclass, so we know what kind of box we're creating

            box_mode = getattr(yex.mode, cls.inside_mode)
            assert box_mode is not None

            original_mode = parser.doc.mode

            t = parser.next(level='querying')
            if isinstance(t, cls):
                logger.debug('%s.from_parser: found a box, %s',
                        cls.__name__, t)
                return t

            parser.push(t)

            logger.debug('%s.from_parser: creating new box, in box_mode %s',
                    cls.__name__, box_mode)

            if parser.optional_string('to'):
                to = Dimen.from_parser(parser)
                spread = None
            elif parser.optional_string('spread'):
                to = None
                spread = Dimen.from_parser(parser)
            else:
                to = None
                spread = None

            parser.eat_optional_spaces()

            opening_symbol = parser.next(level='deep')
            if not isinstance(opening_symbol, yex.parse.BeginningGroup):
                logger.debug( (
                    "%s.from_parser: group didn't begin with "
                    "the opening symbol, but with %s (which is a %s)"),
                    cls.__name__, opening_symbol, type(opening_symbol))

                raise ValueError(
                    f"The group didn't begin with the opening symbol, "
                    f"but with {opening_symbol} "
                    f"(which is a {type(opening_symbol)}."
                    )

            # okay, put it back, or Parser(bounded='single')
            # will get confused
            parser.push(opening_symbol)

            newbox = []
            def handle(result):
                newbox.append(result)

            new_mode = box_mode(
                    doc = parser.doc,
                    to = to,
                    spread = spread,
                    box_type = cls,
                    recipient = handle,
                    )

            parser.doc['_mode'] = new_mode

            logger.debug("%s.from_parser: beginning creation of new box",
                    cls.__name__)

            inner_parser = parser.another(
                    bounded='single',
                    on_eof='exhaust',
                    level='reading',
                    )

            for t in inner_parser:
                logger.debug("%s.from_parser: passing %s to %s",
                        cls.__name__, t, inner_parser.doc.mode)
                inner_parser.doc.mode.handle(
                        item=t,
                        parser=parser,
                        )

            for i in range(2):
                # The nesting of groups can't be more than 2 deeper
                # than the level we started with
                if parser.doc.mode==original_mode:
                    break
                parser.doc.mode.close()

            if not newbox:
                raise ValueError("No box was created!")

            logger.debug("%s.from_parser: new box created: %s",
                    cls.__name__, newbox[0])

            return newbox[0]

class CharBox(Box):
    """
    A Box containing a single character from a font.

    Attributes:
        ch (str): the character
        font (yex.font.Font): the font
        from_ligature (str): the ligature that produced this character,
            or None if there wasn't one. Usually this is None.
            It's only used for diagnostics.
    """
    def __init__(self, font: 'yex.font.Font', ch: str,
                 from_ligature: Union[str,None]=None,
                 ):

        try:
            metric = font.charset[ch]
        except KeyError:
            raise yex.exception.NoSuchCharInFontError(
                    char = ch,
                    font = font,
                    )

        super().__init__(
                height = Dimen.from_another(metric.height),
                width = Dimen.from_another(metric.width),
                depth = Dimen.from_another(metric.depth),
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

    def __getstate__(self) -> str:
        return self.ch

    _symbol_doc = 'the character in the box'

    @property
    def symbol(self) -> str:
        return self.ch
