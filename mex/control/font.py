import logging
from mex.control.word import *
import mex.exception
import mex.filename

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')
general_logger = logging.getLogger('mex.general')

class C_FontControl(C_Expandable):

    def _get_font(self, name, tokens,
            look_up_font = True):

        font_name = tokens.next(
                expand=False,
                on_eof=tokens.EOF_RAISE_EXCEPTION,
                )

        if font_name.category!=font_name.CONTROL:
            raise mex.exception.MexError(
                    f"{name}: Font names must be controls, not {font_name}")

        macros_logger.debug("  -- font name is %s",
                font_name.name)

        if not look_up_font:
            return font_name

        try:
            setter = tokens.state[font_name.name]
        except KeyError:
            raise mex.exception.MexError(
                    f"{name}: There is no such font as {font_name}")

        try:
            result = setter.font
        except AttributeError:
            raise mex.exception.MexError(
                    f"{name}: {font_name} is not a font")

        return result

class C_FontSetter(C_Expandable):
    r"""
    When you use \font to define a font, it puts one of these
    into the controls table. Then when you call it, it changes
    the current font.

    If you subscript it, you can inspect the dimens of the font.
    """
    def __init__(self, font):
        self.font = font

    def __call__(self, name, tokens):
        macros_logger.debug("Setting font to %s",
                self.font.name)
        tokens.state['_currentfont'].value = self.font

    def __getitem__(self, index):
        return self.font[index]

    def __setitem__(self, index, v):
        self.font[index] = v

    def __repr__(self):
        return rf'[font = {self.font.name}]'

class Nullfont(C_FontSetter):
    def __init__(self):
        self.font = mex.font.Nullfont()

class Font(C_FontControl):

    def __call__(self, name, tokens):

        fontname = self._get_font(name, tokens,
                look_up_font = False)

        tokens.eat_optional_equals()

        newfont = mex.font.Font(
                tokens = tokens,
                )

        tokens.state.fonts[newfont.name] = newfont

        new_macro = C_FontSetter(font=newfont)

        tokens.state[fontname.name] = new_macro

        macros_logger.debug("New font setter %s = %s",
                fontname.name,
                new_macro)

class Fontdimen(C_FontControl):

    def _get_params(self, name, tokens):
        which = mex.value.Number(tokens).value

        font = self._get_font(name, tokens,
                look_up_font = False)

        return '%s;%s' % (font.name, which)

    def get_the(self, name, tokens):
        lvalue = self._get_params(name, tokens)

        return str(tokens.state[lvalue])

    def __call__(self, name, tokens):
        lvalue = self._get_params(name, tokens)

        tokens.eat_optional_equals()
        rvalue = mex.value.Dimen(tokens)

        tokens.state[lvalue] = rvalue

class C_Hyphenchar_or_Skewchar(C_FontControl):

    def get_the(self, name, tokens):
        lvalue = self._get_font(name, tokens)

        return str(getattr(lvalue, name.name))

    def __call__(self, name, tokens):
        lvalue = self._get_font(name, tokens)

        tokens.eat_optional_equals()
        rvalue = mex.value.Number(tokens)

        setattr(lvalue,
                name.name,
                rvalue)

class Hyphenchar(C_Hyphenchar_or_Skewchar): pass
class Skewchar(C_Hyphenchar_or_Skewchar): pass
class Fontname(C_Unexpandable): pass

class Textfont(C_FontControl): pass
class Scriptfont(Textfont): pass
class Scriptscriptfont(Textfont): pass
