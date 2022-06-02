"""
Box controls.

These controls create and modify boxes.

The classes implementing the boxes themselves are in `yex.box`.
"""
import logging
from yex.control.control import *
import yex.parse
import yex.exception
import yex.value

logger = logging.getLogger('yex.general')

class C_Box(C_Unexpandable):

    inside_mode = None

    def __call__(self, tokens):
        tokens.push(
                self._construct_box(
                    tokens,
                    )
                )

    def _construct_box(self, tokens):
        """
        Constructs a box.

        You should push all this to the tokeniser, after you've
        messed around with it as you need.

        Specifications for box syntax are on p274 of the TeXbook.

        Args:
            tokens (`Tokeniser`): the tokeniser

        Returns:
            the new box
        """

        if tokens.optional_string('to'):
            to = yex.value.Dimen(tokens)
            spread = None
        elif tokens.optional_string('spread'):
            to = None
            spread = yex.value.Dimen(tokens)
        else:
            to = None
            spread = None

        tokens.eat_optional_spaces()

        newbox = self.our_type(
                to=to,
                spread=spread,
                )

        group = tokens.doc.begin_group(flavour='only-mode')

        if self.inside_mode is not None:
            tokens.doc['_mode'] = self.inside_mode

        logger.debug("%s: beginning creation of %s",
                self, newbox)

        font = tokens.doc['_font']

        interword_space = font[2]
        interword_stretch = font[3]
        interword_shrink = font[4]

        for t in tokens.doc['_mode'].run_single(tokens):
            if isinstance(t, (
                yex.parse.Letter,
                yex.parse.Other,
                )):

                addendum = yex.box.CharBox(font=font, ch=t.ch)

            elif isinstance(t, (
                yex.parse.Space,
                )):

                addendum = yex.box.Leader(
                        space = interword_space,
                        stretch = interword_stretch,
                        shrink = interword_shrink,
                        )
            else:
                addendum = t

            if isinstance(addendum, yex.box.Gismo):
                logger.debug("append %s -> %s",
                        t, newbox)

                newbox.append(addendum)
            else:
                raise yex.exception.YexError(
                        f"{addendum} is of type {type(addendum)}, "
                        f"which can't appear inside {self.identifier}")

        tokens.doc.end_group(
                group = group,
                tokens = tokens,
                )
        logger.debug("%s: creation done: %s",
                self, newbox)

        return newbox

##############################

class Hbox(C_Box):
    our_type = yex.box.HBox
    inside_mode = 'restricted_horizontal'

class Vbox(C_Box):
    our_type = yex.box.VBox
    inside_mode = 'internal_vertical'

class Vtop(C_Box):
    our_type = yex.box.VtopBox
    pass

class Vsplit(C_Box):
    def _construct_box(self, tokens):
        pass # <8bit-number> to <dimen>

class Vcenter(Vbox):
    pass

class Lastbox(C_Box):
    pass

##############################

class Raise(C_Unexpandable):
    our_type = yex.box.HBox
    direction = -1

    vertical = False
    horizontal = True
    math = True

    def __call__(self, tokens):

        distance = yex.value.Dimen(tokens)*self.direction

        logger.debug(
                "%s: will shift by %s: finding contents of new box",
                self,
                distance,
                )

        newbox = tokens.next()

        if not isinstance(newbox, self.our_type):
            raise yex.exception.ParseError(
                    fr"{self}: received {newbox}, which is a {type(newbox)},"
                    "but we needed a {self.our_type}"
                    )

        newbox.shifted_by = distance

        logger.debug(
                "%s: new box is %s",
                self,
                newbox,
                )

        tokens.push(newbox)

class Lower(Raise):
    our_type = yex.box.HBox
    direction = 1

class Moveleft(Raise):
    vertical = True
    horizontal = False
    math = False

    our_type = yex.box.VBox
    direction = -1

class Moveright(Moveleft):
    direction = 1

class C_BoxDimensions(C_Unexpandable):

    dimension = None

    def _get_box(self, tokens):
        which = yex.value.Number(tokens).value
        logger.debug("%s: find box number %s",
                self, which)

        result = tokens.doc.registers['box']. \
                get_directly(which, no_destroy = True)
        logger.debug("%s:   -- it's %s",
                self, result)

        return result

    def get_the(self, tokens):
        box = self._get_box(tokens)

        dimension = self.dimension
        logger.debug("%s:  -- looking up its %s",
                self, dimension)

        result = getattr(box, dimension)

        logger.debug("%s:    -- %s",
                self, result)

        return str(result)

    def __call__(self, tokens):
        raise yex.exception.YexError(
                f"you cannot set the {self.dimension} of a box directly"
                )

class Wd(C_BoxDimensions):
    dimension = 'width'

class Ht(C_BoxDimensions):
    dimension = 'height'

class Dp(C_BoxDimensions):
    dimension = 'depth'

class Setbox(C_Unexpandable):
    def __call__(self, tokens):
        index = yex.value.Number(tokens)
        tokens.eat_optional_equals()

        rvalue = tokens.next(level='executing')

        if not isinstance(rvalue, yex.box.Box):
            raise yex.exception.YexError(
                    f"this was not a box: {rvalue} {type(rvalue)}"
                    )

        tokens.doc[fr'\box{index}'] = rvalue

class Showbox(C_Unexpandable):
    def __call__(self, tokens):
        index = yex.value.Number(tokens)

        box = tokens.doc[fr'\copy{index}'].value

        result = box.showbox()

        print('\n'.join(result))

##############################

class C_Rule(C_Unexpandable):
    """
    Adds a horizontal or vertical rule.

    See p219 of the TeXbook for the syntax rules.
    """

    def __call__(self, tokens):
        tokens.push( self._construct_rule(tokens) )

    def _construct_rule(self, tokens):

        dimensions = self._parse_dimensions(tokens)
        logger.debug("%s: new dimensions are: %s",
                self, dimensions)

        result = yex.box.Rule(
                width = dimensions['width'],
                height = dimensions['height'],
                depth = dimensions['depth'],
                )

        logger.debug("%s:   -- new box is: %s",
                self, result)

        return result

    def _default_dimensions(self):
        raise NotImplementedError()

    def _parse_dimensions(self, tokens):

        result = self._default_dimensions()

        while True:
            tokens.eat_optional_spaces()

            candidate = self._get_letters(tokens)

            if candidate=='':
                return result

            logger.debug("%s: reading the dimension '%s'",
                    self, candidate)

            if candidate not in result:
                logger.debug("%s:   -- that was not a dimension",
                        self)
                tokens.push(candidate)
                return result

            tokens.eat_optional_spaces()
            size = yex.value.Dimen(tokens)
            logger.debug("%s:   -- %s is %s",
                    self, candidate, size)

            result[candidate] = size

    def _get_letters(self, tokens):
        result = ''
        while True:
            t = tokens.next(
                    on_eof = 'none',
                    )

            if not isinstance(t, yex.parse.Letter):
                tokens.push(t)
                return result

            result += t.ch

class Hrule(C_Rule):
    """
    Adds a horizontal rule.
    """
    horizontal = 'vertical'
    vertical = True

    def _default_dimensions(self):
        return {
                'width': 'inherit',
                'height': yex.value.Dimen(0.4, 'pt'),
                'depth': yex.value.Dimen(0),
                }

class Vrule(C_Rule):
    """
    Adds a vertical rule.
    """
    vertical = False
    horizontal = True
    math = False

    def _default_dimensions(self):
        return {
                'width': yex.value.Dimen(0.4, 'pt'),
                'height': 'inherit',
                'depth': 'inherit',
                }

##############################

class C_Skip(C_Unexpandable):
    """
    Adds a horizontal or vertical leader.
    """

    def __call__(self, tokens):
        glue = yex.value.Glue(tokens)
        leader = yex.box.Leader(glue=glue)
        tokens.push(leader)

class Hskip(C_Skip):
    """
    Adds a horizontal leader.
    """
    vertical = False
    horizontal = True
    math = True

class Vskip(C_Skip):
    """
    Adds a vertical leader.
    """
    horizontal = 'vertical'
    vertical = True

##############################

class C_Fill(C_Unexpandable):
    """
    Adds a constant leader.

    See the TeXbook, pp.71-2.
    """

    def __call__(self, tokens):
        leader = yex.box.Leader(glue=self._filler())
        tokens.push(leader)

    def _filler(self):
        raise NotImplementedError()

class Hfil(C_Fill):
    """
    Skips horizontally by zero, but with infinite stretchability and
    shrinkability.
    """
    vertical = False
    horizontal = True
    math = True
    _filler = lambda self: yex.value.Glue(space=0,
            stretch=1, stretch_unit='fil')

class Hfill(Hfil):
    math = False
    """
    Skips horizontally by zero, but with more infinite stretchability.
    """
    _filler = lambda self: yex.value.Glue(space=0,
            stretch=1, stretch_unit='fill')

class Hfilll(Hfill):
    r"""
    Skips horizontally by zero, but with even more infinite stretchability.

    (TeXbook p72: "TeX does not provide a '\vfilll' primitive, since the
    use of this highest infinity is not encouraged.")
    """
    _filler = lambda self: yex.value.Glue(space=0,
            stretch=1, stretch_unit='filll')

class Hss(Hfil):
    """
    Skips horizontally by zero, but with infinite stretchability and
    shrinkability.
    """
    _filler = lambda self: yex.value.Glue(space=0,
            stretch=1, stretch_unit='fil',
            shrink=1, shrink_unit='fil')

class Hfilneg(Hfil):
    r"""
    Cancels the stretchability of a previous \hfil.
    """
    _filler = lambda self: yex.value.Glue(space=0,
            stretch=-1, stretch_unit='fil')

class Vfil(C_Fill):
    """
    Skips vertically by zero, but with infinite stretchability.
    """
    horizontal = 'vertical'
    vertical = True
    _filler = lambda self: yex.value.Glue(space=0,
            stretch=1, stretch_unit='fil')

class Vfill(Vfil):
    """
    Skips vertically by zero, but with more infinite stretchability.
    """
    horizontal = 'vertical'
    vertical = True
    _filler = lambda self: yex.value.Glue(space=0,
            stretch=1, stretch_unit='fill')

class Vss(Vfil):
    """
    Skips vertically by zero, but with infinite stretchability and
    shrinkability.
    """
    _filler = lambda self: yex.value.Glue(space=0,
            stretch=1, stretch_unit='fil',
            shrink=1, shrink_unit='fil')

class Vfilneg(Vfil):
    r"""
    Cancels the stretchability of a previous \vfil.
    """
    _filler = lambda self: yex.value.Glue(space=0,
            stretch=-1, stretch_unit='fil')

##############################

class Mark(C_Unexpandable): pass

class C_Mark(C_Unexpandable): pass
class Firstmark(C_Mark): pass
class Botmark(C_Mark): pass
class Splitfirstmark(C_Mark): pass
class Splitbotmark(C_Mark): pass
class Topmark(C_Mark): pass

class Leaders(C_Unexpandable): pass
class Cleaders(Leaders): pass
class Xleaders(Leaders): pass

class C_Unsomething(C_Unexpandable): pass
class Unpenalty(C_Unsomething): pass
class Unkern(C_Unsomething): pass
class Unskip(C_Unsomething): pass
