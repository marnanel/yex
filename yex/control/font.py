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

    def __init__(self, font, name):

        if not isinstance(font, yex.font.Font):
            raise ValueError(
                    f"Needed a font (and not {font}, which is a {type(font)}")

        self.font = font
        self.name = name

    def __call__(self, tokens):
        logger.debug("Setting font to %s, via the control %s",
                self.font.name, self.name)
        tokens.doc['_font'] = self.font

    def get_element(self, index):
        return self.font[index]

    __getitem__=get_element

    def __repr__(self):
        return rf'[font setter = {self.font.name}]'

    @property
    def identifier(self):
        return self.name

    def __getstate__(self):
        result = dict(self.font.__getstate__())
        result['setter'] = self.name
        return result

    @classmethod
    def from_tokens(cls, tokens):
        result = tokens.next(
                level = 'querying',
                on_eof='raise',
                )

        logger.debug("  -- font setter name is %s",
                result)

        if not isinstance(result, cls):
            raise yex.exception.NeededFontSetterError(
                    problem=result,
                    )

        return result

class Nullfont(C_FontSetter):
    """
    Selects the null font, which contains no characters.

    The constructor's "doc" parameter exists so that the class
    object Nullfont can be placed in the controls table at the
    start of a run. Other C_Fontsetter instances don't need this.
    They're placed during the run, so they're placed
    as instances rather than as their class object.
    """

    def __init__(self, doc=None):
        super().__init__(
                font = yex.font.Nullfont(),
                name = r'nullfont',
                )

class Font(C_Unexpandable):

    def __call__(self, tokens):

        fontname = tokens.next(
                level = 'deep',
                on_eof='raise',
                )
        if not isinstance(fontname, yex.parse.Control):
            raise yex.exception.YexError(
                    f'Expected a control name, and not '
                    f'{fontname} (which is a {fontname}).'
                    )

        tokens.eat_optional_char('=')

        logger.debug("looking for the font to call %s",
                fontname)

        newfont = yex.font.Font.from_tokens(tokens)

        logger.debug("so the font %s will be %s",
                newfont,
                fontname)

        tokens.doc.fonts[newfont.name] = newfont

        new_control = C_FontSetter(
                font=newfont,
                name=fontname.name,
                )

        tokens.doc[fontname.identifier] = new_control

        logger.debug("New font setter %s = %s",
                fontname,
                new_control)

    @classmethod
    def from_serial(self, state):

        s = dict(state)

        setter = s['setter']
        del s['setter']

        font = yex.font.Font.from_serial(s)
        result = C_FontSetter(font=font, name=s)

        return result

class Fontdimen(C_Unexpandable):
    """
    Gets and sets various details of a font.

    Parameters:
        1. the identifier of the font
        2. the number of the detail. See yex.font.Font for the meanings
            of these numbers.
    """

    def _get_params(self, tokens):
        which = yex.value.Number.from_tokens(tokens).value

        fontname = C_FontSetter.from_tokens(tokens)

        return fr'\{fontname.name};{which}'

    def get_the(self, tokens):
        lvalue = self._get_params(tokens)

        return str(tokens.doc[lvalue])

    def __call__(self, tokens):
        lvalue = self._get_params(tokens)

        tokens.eat_optional_char('=')
        rvalue = yex.value.Dimen.from_tokens(tokens)

        tokens.doc[lvalue] = rvalue

class C_Hyphenchar_or_Skewchar(C_Unexpandable):

    def get_the(self, tokens):
        lvalue = C_FontSetter.from_tokens(tokens).value

        return str(getattr(lvalue, self.name))

    def __call__(self, tokens):
        lvalue = C_FontSetter.from_tokens(tokens).value

        tokens.eat_optional_char('=')
        rvalue = yex.value.Number.from_tokens(tokens)

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
