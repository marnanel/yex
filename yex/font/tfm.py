import struct
import os
import math
import warnings
from yex.font.font import Font
import yex.logging
import yex.value
import yex.font.pk
import fontTools.tfmLib

logger = yex.logging.getLogger('font')

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
    def __init__(self,
            f,
            size = None,
            scale = None,
            *args, **kwargs,
            ):

        super().__init__(f, *args, **kwargs)

        self._tfm = fontTools.tfmLib.TFM(f)

        self.size = size
        self.scale = scale
        self.metrics = Metrics(
                parent = self,
                )
        self._glyphs = None

        self.param_names = ['']
        self.param_names.extend(
                fontTools.tfmLib.BASE_PARAMS
                )

    @property
    def glyphs(self):
        if self._glyphs is None:
            self._glyphs = Font.from_name(
                os.path.splitext(self.source)[0]+'.pk',
                )

        return self._glyphs

    def points_to_dimen(self, points):
        return yex.value.Dimen(points * self._tfm.designsize, 'pt')

class CharacterMetric:
    def __init__(self, parent, contents):
        self.parent = parent
        self.contents = contents

    def _get(self, field):
        if field in self.contents:
            return self.parent.points_to_dimen(self.contents[field])
        else:
            return yex.value.Dimen()

    @property
    def height(self):
        return self._get('height')

    @property
    def width(self):
        return self._get('width')

    @property
    def depth(self):
        return self._get('depth')

    @property
    def italic_correction(self):
        return self._get('italic')

class Metrics:
    def __init__(self, parent):
        self.parent = parent

    def get_character(self, codepoint):
        return CharacterMetric(
                parent = self.parent,
                contents = self.parent._tfm.chars[codepoint],
                )

    @property
    def dimens(self):
        return self

    def __getitem__(self, key):
        result = self.parent.points_to_dimen(
                self.parent._tfm.fontdimens[
                    self.parent.param_names[key]
                    ])
        return result

    def __contains__(self, key):
        return key>0 and key<len(self.parent.param_names)

    def keys(self):
        return self.parent._tfm.fontdimens.keys()

    def items(self):
        return self.parent._tfm.fontdimens.items()

    @property
    def kerns(self):
        return self.parent._tfm.kerning

    @property
    def ligatures(self):
        return self.parent._tfm.ligatures
