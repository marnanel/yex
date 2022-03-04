import logging
from mex.control.word import C_ControlWord
import mex.exception
import mex.value

commands_logger = logging.getLogger('mex.commands')

class _Hvbox(C_ControlWord):

    def __call__(self, name, tokens):
        for token in tokens:
            if token.category == token.BEGINNING_GROUP:
                # good
                break

            raise mex.exception.MexError(
                    f"{name} must be followed by a group")

        tokens.state.begin_group()
        tokens.state['_mode'] = self.next_mode

class Hbox(_Hvbox):
    next_mode = 'restricted_horizontal'

class Vbox(_Hvbox):
    next_mode = 'internal_vertical'

class C_BoxDimensions(C_ControlWord):

    dimension = None

    def _get_box(self, name, tokens):
        which = mex.value.Number(tokens).value
        commands_logger.debug("%s: find box number %s",
                name, which)

        result = tokens.state.registers['box'][which]
        commands_logger.debug("%s:   -- it's %s",
                name, result)

        return result

    def get_the(self, name, tokens):
        box = self._get_box(name, tokens)

        dimension = self.dimension
        commands_logger.debug("%s:  -- looking up its %s",
                name, dimension)

        result = getattr(box.value, dimension)

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

        tokens.state[f'box{lvalue}'] = rvalue
