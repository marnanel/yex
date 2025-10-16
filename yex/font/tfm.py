import struct
import os
import math
import warnings
from yex.font.font import Font, Metrics, Character
import yex.logging
import yex.value
import yex.font.pk
import fontTools.tfmLib
from typing import Union

logger = yex.logging.getLogger('font')

class _TfmCharacter(Character):
    def _get(self, field):
        contents = self.font._tfm.chars[self.codepoint]
        if field in contents:
            return self.font.points_to_dimen(contents[field])
        else:
            return yex.value.Dimen()

class _TfmMetrics(Metrics):
    def __init__(self, font):
        self.font = font

    @property
    def dimens(self):
        return self

    def __contains__(self, key):
        return key>0 and key<len(self.font.param_names)

    def __getitem__(self, v):
        return self.font._tfm.fontdimens[v]

    def keys(self):
        return self.font._tfm.fontdimens.keys()

    def items(self):
        return self.font._tfm.fontdimens.items()

    @property
    def kerns(self):
        return self.font._tfm.kerning

    @property
    def ligatures(self):
        return self.font._tfm.ligatures

class Tfm(Font):
    """
    A font in TeX's own TFM format ("TeX Font Metrics").

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

    character_class = _TfmCharacter
    metrics_class = _TfmMetrics

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

        self.param_names = ['']
        self.param_names.extend(
                fontTools.tfmLib.BASE_PARAMS
                )

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
