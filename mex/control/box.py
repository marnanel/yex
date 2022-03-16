import logging
from mex.control.word import *
import mex.parse
import mex.exception
import mex.value

commands_logger = logging.getLogger('mex.commands')

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
            to = mex.value.Dimen(tokens)
            spread = None
        elif tokens.optional_string('spread'):
            to = None
            spread = mex.value.Dimen(tokens)
        else:
            to = None
            spread = None

        tokens.eat_optional_spaces()
        token = tokens.next(on_eof=tokens.EOF_RAISE_EXCEPTION)
        if token.category == token.BEGINNING_GROUP:
            # good
            tokens.push(token)
        else:
            raise mex.exception.MexError(
                    f"{name} must be followed by "
                    "'{'"
                    f"(not {token.category})")

        newbox = self.our_type(
                to=to,
                spread=spread,
                )

        tokens.state.begin_group()

        if self.inside_mode is not None:
            tokens.state['_mode'] = self.inside_mode

        pushback = []

        commands_logger.debug("%s: beginning creation of %s",
                self, newbox)

        for t in tokens.single_shot():

            if isinstance(t, mex.parse.Token):

                if t.category in (t.LETTER, t.OTHER):
                    font = tokens.state['_font']
                    addendum = mex.box.CharBox(font=font, ch=t.ch)
                elif t.category in (t.SPACE,):
                    addendum = mex.gismo.Leader() # TODO
                else:
                    addendum = t
            else:
                addendum = t

            if isinstance(addendum, mex.gismo.Gismo):
                commands_logger.debug("append %s -> %s",
                        t, self)

                newbox.append(addendum)
            else:
                raise mex.exception.MexError(
                        f"{addendum} is of type {type(addendum)}, "
                        f"which can't appear in a {name}")

        tokens.state.end_group()

        commands_logger.debug("%s: creation done: %s",
                self, newbox)
        commands_logger.debug("%s:   -- with pushback: %s",
                self, pushback)

        pushback.append(newbox)

        return pushback

##############################

class Hbox(C_Box):
    our_type = mex.box.HBox
    inside_mode = 'restricted_horizontal'

class Vbox(C_Box):
    our_type = mex.box.VBox
    inside_mode = 'internal_vertical'

class Vtop(C_Box):
    our_type = mex.box.VtopBox
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
    our_type = mex.box.HBox
    direction = -1

    vertical = False
    horizontal = True
    math = True

    def __call__(self, name, tokens):

        distance = mex.value.Dimen(tokens)*self.direction

        commands_logger.debug(
                "%s: will shift by %s: finding contents of new box",
                name,
                distance,
                )

        newbox = tokens.next()

        if not isinstance(newbox, self.our_type):
            raise mex.exception.ParseError(
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
    our_type = mex.box.HBox
    direction = 1

class Moveleft(Raise):
    vertical = True
    horizontal = False
    math = False

    our_type = mex.box.VBox
    direction = -1

class Moveright(Moveleft):
    direction = 1

class C_BoxDimensions(C_Expandable):

    dimension = None

    def _get_box(self, name, tokens):
        which = mex.value.Number(tokens).value
        commands_logger.debug("%s: find box number %s",
                name, which)

        result = tokens.state.registers['box']. \
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
        raise mex.exception.MexError(
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
        index = mex.value.Number(tokens)
        tokens.eat_optional_equals()

        rvalue = tokens.next()

        if not isinstance(rvalue, mex.box.Box):
            raise mex.exception.MexError(
                    f"this was not a box: {rvalue}"
                    )

        tokens.state[f'box{index}'] = rvalue

class Showbox(C_Expandable):
    def __call__(self, name, tokens):
        index = mex.value.Number(tokens)

        box = tokens.state[f'copy{index}'].value

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
