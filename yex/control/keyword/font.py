"""
Font controls.
"""
import logging
import yex
from yex.control import Unexpandable, FontSetter

logger = logging.getLogger('yex.general')

class Nullfont(FontSetter):
    """
    Selects the null font, which contains no characters.

    The constructor's "doc" parameter exists so that the class
    object Nullfont can be placed in the controls table at the
    start of a run. Other Fontsetter instances don't need this.
    They're placed during the run, so they're placed
    as instances rather than as their class object.
    """

    def __init__(self, doc=None):
        super().__init__(
                font = yex.font.Nullfont(),
                name = r'nullfont',
                )

class Tenrm(FontSetter):
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

class Font(Unexpandable):

    def __call__(self, tokens):

        fontname = tokens.next(
                level = 'deep',
                on_eof='raise',
                )
        if not isinstance(fontname, yex.parse.Control):
            raise yex.exception.NeededNewFontNameError(
                    problem = fontname,
                    )

        tokens.eat_optional_char('=')

        logger.debug("looking for the font to call %s",
                fontname)

        newfont = yex.font.Font.from_tokens(tokens)

        logger.debug("so the font %s will be %s",
                newfont,
                fontname)

        tokens.doc.fonts[newfont.name] = newfont

        new_control = FontSetter(
                font=newfont,
                name=fontname.name,
                )

        # Delete the entry first, so there's no chance that
        # the Document will take this as a request to set the
        # value of the FontSetter.
        try:
            del tokens.doc[fontname.identifier]
        except KeyError:
            pass

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
        result = FontSetter(font=font, name=s)

        return result

@yex.decorator.control()
def Fontdimen(index: int, fontsetter: FontSetter, optional_equals,
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
def Fontdimen_query(index: int, fontsetter: FontSetter):
    return fontsetter.get_element(index)

@yex.decorator.control()
def Hyphenchar(fontsetter: FontSetter, value: int):
    r"""
    Sets the character used for hyphenation.

    If this is -1, hyphenation is turned off.

    By default, this has the value of \defaulthyphenchar.
    By default, *that* has the value 45, which is the
    ASCII code for a hyphen.
    """
    fontsetter.value.hyphenchar = value

@Hyphenchar.on_query()
def Hyphenchar_query(fontsetter: FontSetter):
    return fontsetter.value.hyphenchar

@yex.decorator.control()
def Skewchar(fontsetter: FontSetter, value: int):
    fontsetter.value.skewchar = value

@Skewchar.on_query()
def Skewchar_query(fontsetter: FontSetter):
    return fontsetter.value.skewchar

class Fontname(Unexpandable):
    """
    Inserts the name of the current font.
    """

class A_002f(Unexpandable): # slash
    """
    Adds an italic correction.
    """
