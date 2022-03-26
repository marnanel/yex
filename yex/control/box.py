import logging
from yex.control.word import *
import yex.parse
import yex.exception
import yex.value

commands_logger = logging.getLogger('yex.commands')

class C_Box(C_Expandable):

    inside_mode = None

    def __call__(self, name, tokens):
        tokens.push(
                self._construct_box(
                    name,
                    tokens,
                    )
                )

    def _construct_box(self, name, tokens):
        """
        Constructs a box.

        Returns a list. The new box is the last item in the list.
        Before it, there are any control words which we found
        during parsing, in the order they were found.

        You should push all this to the tokeniser, after you've
        messed around with it as you need.

        Specifications for box syntax are on p274 of the TeXbook.
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
        token = tokens.next(on_eof=tokens.EOF_RAISE_EXCEPTION)
        if token.category == token.BEGINNING_GROUP:
            # good
            tokens.push(token)
        else:
            raise yex.exception.YexError(
                    f"{name} must be followed by "
                    "'{'"
                    f"(not {token.category})")

        newbox = self.our_type(
                to=to,
                spread=spread,
                )

        tokens.doc.begin_group()

        if self.inside_mode is not None:
            tokens.doc['_mode'] = self.inside_mode

        pushback = []

        commands_logger.debug("%s: beginning creation of %s",
                self, newbox)

        font = tokens.doc['_font']

        interword_space = font[2]
        interword_stretch = font[3]
        interword_shrink = font[4]

        for t in tokens.single_shot():

            if isinstance(t, yex.parse.Token):

                if t.category in (t.LETTER, t.OTHER):
                    addendum = yex.box.CharBox(font=font, ch=t.ch)
                elif t.category in (t.SPACE,):
                    addendum = yex.gismo.Leader(
                            space = interword_space,
                            stretch = interword_stretch,
                            shrink = interword_shrink,
                            )
                else:
                    addendum = t
            else:
                addendum = t

            if isinstance(addendum, yex.gismo.Gismo):
                commands_logger.debug("append %s -> %s",
                        t, self)

                newbox.append(addendum)
            else:
                raise yex.exception.YexError(
                        f"{addendum} is of type {type(addendum)}, "
                        f"which can't appear in a {name}")

        tokens.doc.end_group()

        commands_logger.debug("%s: creation done: %s",
                self, newbox)
        commands_logger.debug("%s:   -- with pushback: %s",
                self, pushback)

        pushback.append(newbox)

        return pushback

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
    def _construct_box(self, name, tokens):
        pass # <8bit-number> to <dimen>

class Vcenter(Vbox):
    pass

class Lastbox(C_Box):
    pass

##############################

class Raise(C_Expandable):
    our_type = yex.box.HBox
    direction = -1

    vertical = False
    horizontal = True
    math = True

    def __call__(self, name, tokens):

        distance = yex.value.Dimen(tokens)*self.direction

        commands_logger.debug(
                "%s: will shift by %s: finding contents of new box",
                name,
                distance,
                )

        newbox = tokens.next()

        if not isinstance(newbox, self.our_type):
            raise yex.exception.ParseError(
                    fr"{name}: received {newbox}, which is a {type(newbox)},"
                    "but we needed a {self.our_type}"
                    )

        newbox.shifted_by = distance

        commands_logger.debug(
                "%s: new box is %s",
                name,
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

class C_BoxDimensions(C_Expandable):

    dimension = None

    def _get_box(self, name, tokens):
        which = yex.value.Number(tokens).value
        commands_logger.debug("%s: find box number %s",
                name, which)

        result = tokens.doc.registers['box']. \
                get_directly(which, no_destroy = True)
        commands_logger.debug("%s:   -- it's %s",
                name, result)

        return result

    def get_the(self, name, tokens):
        box = self._get_box(name, tokens)

        dimension = self.dimension
        commands_logger.debug("%s:  -- looking up its %s",
                name, dimension)

        result = getattr(box, dimension)

        commands_logger.debug("%s:    -- %s",
                name, result)

        return str(result)

    def __call__(self, name, tokens):
        raise yex.exception.YexError(
                f"you cannot set the {self.dimension} of a box directly"
                )

class Wd(C_BoxDimensions):
    dimension = 'width'

class Ht(C_BoxDimensions):
    dimension = 'height'

class Dp(C_BoxDimensions):
    dimension = 'depth'

class Setbox(C_Expandable):
    def __call__(self, name, tokens):
        index = yex.value.Number(tokens)
        tokens.eat_optional_equals()

        rvalue = tokens.next()

        if not isinstance(rvalue, yex.box.Box):
            raise yex.exception.YexError(
                    f"this was not a box: {rvalue}"
                    )

        tokens.doc[fr'\box{index}'] = rvalue

class Showbox(C_Expandable):
    def __call__(self, name, tokens):
        index = yex.value.Number(tokens)

        box = tokens.doc[fr'\copy{index}'].value

        result = box.showbox()

        print('\n'.join(result))

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
