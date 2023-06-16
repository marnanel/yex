"""
A class of controls to select a font.
"""
import logging
import yex
from yex.control.control import Expandable, Unexpandable

logger = logging.getLogger('yex.general')

class FontSetter(Unexpandable):
    r"""
    When you use \font to define a font, it puts one of these
    into the controls table. Then when you call it, it changes
    the current font.

    If you subscript it, you can inspect the dimens of the font.
    """

    is_queryable = True

    def __init__(self, font, name, control_name = None):

        if not isinstance(font, yex.font.Font):
            raise ValueError(
                    f"Needed a font (and not {font}, which is a {type(font)}")

        self.font = font
        self.name = name
        self.control_name = control_name or name

    def __call__(self, tokens):
        logger.debug("Setting font to %s, via the control %s",
                self.font.name, self.name)
        tokens.doc['_font'] = self.font

    @property
    def value(self):
        # You can read it, but you may not set it.
        return self.font

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
