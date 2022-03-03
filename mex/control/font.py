import logging
from mex.control.word import C_ControlWord, C_Defined
import mex.exception
import mex.filename

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')
general_logger = logging.getLogger('mex.general')

class Font(C_ControlWord):
    """
    TODO
    """ # TODO

    def __call__(self, name, tokens):

        tokens.running = False
        fontname = tokens.__next__()
        tokens.running = True

        tokens.eat_optional_equals()

        newfont = mex.font.Font(
                tokens = tokens,
                )

        tokens.state.fonts[newfont.name] = newfont

        class Font_setter(C_ControlWord):
            def __call__(self, name, tokens):
                macros_logger.debug("Setting font to %s",
                        newfont.name)
                tokens.state['_currentfont'].value = newfont

            @property
            def font(self):
                return newfont

            def __getitem__(self, index):
                return newfont[index]

            def __setitem__(self, index, v):
                newfont[index] = v

            def __repr__(self):
                return rf'[font = {newfont.name}]'

        new_macro = Font_setter()

        tokens.state[fontname.name] = new_macro

        macros_logger.debug("New font setter %s = %s",
                fontname.name,
                new_macro)

class Fontdimen(C_ControlWord):

    def _get_params(self, tokens):
        which = mex.value.Number(tokens).value

        for font_name in tokens:
            break
        if font_name.category!=font_name.CONTROL:
            raise mex.exception.MexError(
                    f"Font names must be controls, not {font_name}")

        return '%s%s' % (font_name.name, which)

    def get_the(self, tokens):
        lvalue = self._get_params(tokens)

        try:
            return str(tokens.state[lvalue])
        except KeyError:
            raise mex.exception.MexError(
                    f"There is no such font")

    def __call__(self, name, tokens):
        lvalue = self._get_params(tokens)

        tokens.eat_optional_equals()
        rvalue = mex.value.Dimen(tokens)

        try:
            tokens.state[lvalue] = rvalue
        except KeyError:
            raise mex.exception.MexError(
                    f"There is no such font")
