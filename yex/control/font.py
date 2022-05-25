"""
Font controls.
"""
import logging
from yex.control.control import *
import yex.exception
import yex.filename
import yex.font
import yex.parse

logger = logging.getLogger('yex.general')

class C_FontSetter(C_Unexpandable):
    r"""
    When you use \font to define a font, it puts one of these
    into the controls table. Then when you call it, it changes
    the current font.

    If you subscript it, you can inspect the dimens of the font.
    """
    def __init__(self, font):

        if not isinstance(font, yex.font.Font):
            raise yex.exception.YexError(f"internal: {type(font)} is not a font!")

        self.value = font

    def __call__(self, tokens):
        logger.debug("Setting font to %s",
                self.value.name)
        tokens.doc['_font'] = self.value

    def __getitem__(self, index):
        return self.value[index]

    def __setitem__(self, index, v):
        self.value[index] = v

    def __repr__(self):
        return rf'[font setter = {self.value.name}]'

    @property
    def identifier(self):
        return self.value.name

class Nullfont(C_FontSetter):
    """
    Selects the null font, which contains no characters.
    """

    def __init__(self):
        super().__init__(
                font = yex.font.Nullfont(),
                )

class Font(C_Unexpandable):

    def __call__(self, tokens):

        fontname = tokens.next(
                level = 'deep',
                on_eof='raise',
                )

        tokens.eat_optional_equals()

        logger.debug("looking for the font to call %s",
                fontname)

        newfont = yex.font.get_font_from_tokens(tokens)

        logger.debug("so the font %s will be %s",
                newfont,
                fontname)

        tokens.doc.fonts[newfont.name] = newfont

        new_control = C_FontSetter(font=newfont)

        tokens.doc[fontname.identifier] = new_control

        logger.debug("New font setter %s = %s",
                fontname,
                new_control)

class C_FontControl(C_Unexpandable):

    def _get_font_via_setter_name(self, tokens):
        fontname = tokens.next(
                level = 'querying',
                on_eof='raise',
                )

        logger.debug("  -- font setter name is %s",
                fontname)

        if not isinstance(fontname, C_FontSetter):
            raise yex.exception.ParseError(
                    "{fontname} is not a font setter control")

        result = fontname.value

        logger.debug("    -- so the font is %s (of type %s)",
                result, type(result))

        return result

class Fontdimen(C_FontControl):
    """
    Gets and sets various details of a font.

    Parameters:
        1. the identifier of the font
        2. the number of the detail. See yex.font.Font for the meanings
            of these numbers.
    """

    def _get_params(self, tokens):
        which = yex.value.Number(tokens).value

        font = self._get_font_via_setter_name(tokens)

        return r'%s;%s' % (font.identifier, which)

    def get_the(self, tokens):
        lvalue = self._get_params(tokens)

        return str(tokens.doc[lvalue])

    def __call__(self, tokens):
        lvalue = self._get_params(tokens)

        tokens.eat_optional_equals()
        rvalue = yex.value.Dimen(tokens)

        tokens.doc[lvalue] = rvalue

class C_Hyphenchar_or_Skewchar(C_FontControl):

    def get_the(self, tokens):
        lvalue = self._get_font_via_setter_name(tokens)

        return str(getattr(lvalue, self.name))

    def __call__(self, tokens):
        lvalue = self._get_font_via_setter_name(tokens)

        tokens.eat_optional_equals()
        rvalue = yex.value.Number(tokens)

        setattr(lvalue,
                self.name,
                rvalue)

class Hyphenchar(C_Hyphenchar_or_Skewchar):
    r"""
    Sets the character used for hyphenation.

    If this is -1, hyphenation is turned off.

    By default, this has the value of \defaulthyphenchar.
    By default, *that* has the value 45, which is the
    ASCII code for a hyphen.
    """

class Skewchar(C_Hyphenchar_or_Skewchar): pass

class Fontname(C_Unexpandable):
    """
    Inserts the name of the current font.
    """

class A_002f(C_Unexpandable): # slash
    """
    Adds an italic correction.
    """
