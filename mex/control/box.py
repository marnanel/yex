import logging
from mex.control.word import C_ControlWord
import mex.parse
import mex.exception
import mex.value

commands_logger = logging.getLogger('mex.commands')

class C_Hvbox(C_ControlWord):

    def __call__(self, name, tokens):
        for token in tokens:
            if token.category == token.BEGINNING_GROUP:
                # good
                tokens.push(token)
                break

            raise mex.exception.MexError(
                    f"{name} must be followed by a group")

        newbox = self.our_type()

        tokens.state.begin_group()
        tokens.state['_mode'] = self.next_mode

        font = tokens.state['_currentfont'].value

        e = mex.parse.Expander(
                tokens,
                single = True,
                )

        pushback = []

        commands_logger.debug("%s: beginning creation of %s",
                self, newbox)

        for t in e:

            if isinstance(t, mex.parse.Token):

                if t.category in (t.LETTER, t.OTHER):
                    addendum = mex.box.CharBox(font=font, ch=t.ch)
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
                t, newbox)
        commands_logger.debug("%s:   -- with pushback: %s",
                t, pushback)

        pushback.append(newbox)

        tokens.push(pushback)

class Hbox(C_Hvbox):
    our_type = mex.box.HBox
    next_mode = 'restricted_horizontal'

class Vbox(C_Hvbox):
    our_type = mex.box.VBox
    next_mode = 'internal_vertical'

class C_BoxDimensions(C_ControlWord):

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

class Setbox(C_ControlWord):
    def __call__(self, name, tokens):
        index = mex.value.Number(tokens)
        tokens.eat_optional_equals()

        e = mex.parse.Expander(
                tokens,
                )
        for rvalue in e:
            break

        if not isinstance(rvalue, mex.box.Box):
            raise mex.exception.MexError(
                    "this was not a box"
                    )

        tokens.state[f'box{index}'] = rvalue
