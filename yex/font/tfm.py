import struct
import os
import math
import warnings
from yex.font.font import Font, _Metrics, _Character, _Charset
import yex.logging
import yex.value
import yex.font.pk
import fontTools.tfmLib
from typing import Union, Type

logger = yex.logging.getLogger('font')

class _TfmCharacter(_Character):
    def _get(self, field):
        contents = self.font._tfm.chars[self.codepoint]
        if field in contents:
            return self.font.points_to_dimen(contents[field])
        else:
            return yex.value.Dimen()

class _TfmCharset(_Charset):
    pass

class _TfmMetrics(_Metrics):

    TFM_DIMEN_NAMES = (
            [None] +
            fontTools.tfmLib.BASE_PARAMS +
            fontTools.tfmLib.MATHSY_PARAMS +
            fontTools.tfmLib.MATHEX_PARAMS
            )

    DIMEN_MULTIPLICAND = 10.0 # but why?

    def __init__(self, font):
        self.font = font

    @property
    def dimens(self):
        return self

    def __contains__(self, key):
        return (
                key>=0 and key<len(self.TFM_DIMEN_NAMES) and
                self.TFM_DIMEN_NAMES[key] in self.font._tfm.fontdimens
                )

    def __getitem__(self, v):
        return yex.value.Dimen(
                self.font._tfm.fontdimens[
                    self.TFM_DIMEN_NAMES[v]
                    ] * self.DIMEN_MULTIPLICAND)

    def keys(self):
        return [
            self.TFM_DIMEN_NAMES.index(s)
            for s in self.font._tfm.fontdimens.keys()
            ]

    def items(self):
        return [
                (self.TFM_DIMEN_NAMES.index(f),
                 yex.value.Dimen(v * self.DIMEN_MULTIPLICAND))
                for f,v in self.font._tfm.fontdimens.items()
                ]

    @property
    def kerns(self):
        return self.font._tfm.kerning

    @property
    def ligatures(self):
        return self.font._tfm.ligatures

class Tfm(Font):
    """
    A font in TeX's own TFM format ("TeX Font _Metrics").

    TFM files don't contain the glyphs. If you call `glyphs()` on
    a Tfm object, it looks up the corresponding .pk file, which
    should contain the glyphs you need. See `yex.font.pk` for that.

    The format was devised by Lyle Harold in 1980.

    This class used to do the parsing, but now it's done by fontTools,
    and this is just a wrapper.

    Descriptions of the format:
        * Fuchs, "TeX Font Metric files", TUGboat vol 2 no 1, February 1981:
            https://tug.org/TUGboat/Articles/tb02-1/tb02fuchstfm.pdf
        * the comments around line 10400 of tex.web
        * src/utils/tfmtodit/tfmtodit.cpp in groff
    """

    character_class:Type = _TfmCharacter
    charset_class:Type = _TfmCharset
    metrics_class:Type = _TfmMetrics

    def __init__(self,
            f,
                 size: Union[yex.value.Dimen, None] = None,
                 scale: Union[yex.value.Dimen, None] = None,
                 *args, **kwargs,
            ):

        super().__init__(f, *args, **kwargs)

        self._tfm = fontTools.tfmLib.TFM(f)

        self.size = size
        self.scale = scale
        self._glyphs = None

    @property
    def glyphs(self):
        if self._glyphs is None:
            self._glyphs = Font._from_name(
                os.path.splitext(self.source)[0]+'.pk',
                find_pk = True,
                )

        return self._glyphs

    def points_to_dimen(self,
                        points:float,
                        ) -> yex.value.Dimen:
        return yex.value.Dimen(points * self._tfm.designsize, 'pt')
