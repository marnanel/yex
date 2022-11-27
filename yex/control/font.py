"""
Font controls.
"""
import logging
from yex.control.control import *
from yex.control.array import C_Array
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

    is_queryable = True

    def __init__(self, font, name):

        if not isinstance(font, yex.font.Font):
            raise ValueError(
                    f"Needed a font (and not {font}, which is a {type(font)}")

        self.value = font
        self.name = name

    def __call__(self, tokens):
        logger.debug("Setting font to %s, via the control %s",
                self.value.name, self.name)
        tokens.doc['_font'] = self.value

    def get_element(self, index):
        return self.value[index]

    __getitem__=get_element

    def __repr__(self):
        return rf'[font setter = {self.value.name}]'

    @property
    def identifier(self):
        return self.name

    def __getstate__(self):
        result = dict(self.value.__getstate__())
        result['setter'] = self.name
        return result

    @classmethod
    def from_tokens(cls, tokens):
        result = tokens.next(
                level = 'reading',
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

class Tenrm(C_FontSetter):
    r"""
    Selects the default font.

    This only exists in the initial controls table because the default
    font (yex.font.Default) must identify itself as "\tenrm" for
    compatibility with TeX.
    """

    def __init__(self, doc=None):
        super().__init__(
                font = yex.font.Default(),
                name = r'tenrm',
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

@yex.decorator.control()
def Fontdimen(index: int, fontsetter: C_FontSetter, optional_equals,
        rvalue: yex.value.Dimen):
    """
    Various details of a font.

    Parameters:
        1. the identifier of the font
        2. the number of the detail. See yex.font.Font for the meanings
            of these numbers.
    """
    logger.debug(r"\fontdimen: about to set the dimensions of a font.")
    fontsetter.value[index] = rvalue

@Fontdimen.on_query()
def Fontdimen_query(index: int, fontsetter: C_FontSetter):
    return fontsetter.get_element(index)

@yex.decorator.control()
def Hyphenchar(fontsetter: C_FontSetter, value: int):
    r"""
    Sets the character used for hyphenation.

    If this is -1, hyphenation is turned off.

    By default, this has the value of \defaulthyphenchar.
    By default, *that* has the value 45, which is the
    ASCII code for a hyphen.
    """
    fontsetter.value.hyphenchar = value

@Hyphenchar.on_query()
def Hyphenchar_query(fontsetter: C_FontSetter):
    return fontsetter.value.hyphenchar

@yex.decorator.control()
def Skewchar(fontsetter: C_FontSetter, value: int):
    fontsetter.value.skewchar = value

@Skewchar.on_query()
def Skewchar_query(fontsetter: C_FontSetter):
    return fontsetter.value.skewchar

class Fontname(C_Unexpandable):
    """
    Inserts the name of the current font.
    """

class A_002f(C_Unexpandable): # slash
    """
    Adds an italic correction.
    """
