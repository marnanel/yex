import yex
from yex.font.tfm import Tfm, CharacterMetric
from yex.value import Dimen
from yex.filename import Filename

class Default(Tfm):
    """
    The metrics for the font `cmr10`, hard-coded.

    It exists because `cmr10` is the default font, and every Document
    containing at least one symbol attempts to access it. So, if there's
    any problem loading the external file `cmr10.tfm`, every Document
    will break.

    Just like the real font metrics, it doesn't contain the glyphs.
    If you look them up using the `glyphs` attribute,
    it will load them from `cmr10.pk`.

    You can get hold of the singleton instance of this font using
    ```
    Font.from_name(None)
    ```

    If you do
    ```
    Font.from_name("cmr10")
    ```
    you will still get the metrics for `cmr10`.

    At the end of this module, there is some code which loads the
    real `cmr10.fnt` and produces the values for this class.
    Its output will need some rearranging before it fits the actual code.
    """

    def __init__(self,
            name = 'tenrm', # the name of this font in the controls table
            ):
        self.hyphenchar = 45
        self.size = Dimen(10, 'pt')
        self.scale = None
        self.skewchar = -1
        self.used = set()
        self.metrics = DefaultMetrics()
        self._glyphs = None
        self._custom_dimens = {}
        self.name = name or 'tenrm'
        self.source = 'cmr10'

    def __getstate__(self):
        return super().__getstate__(name = ['tenrm'])

    @property
    def glyphs(self):
        if self._glyphs is None:
            self._glyphs = self.from_name('cmr10.pk')

        return self._glyphs

class DefaultMetrics:

    def __init__(self):
        self.character_coding_scheme = b'TeX text'
        self.checksum = 1274110073
        self.design_size = yex.value.Dimen(655360, 'sp')
        self.first_char = 0
        self.font_identifier = b'CMR'
        self.last_char = 127
        self.ligatures = {
            '\x0bi': '\x0e',
            '\x0bl': '\x0f',
            '!`': '<',
            "''": '"',
            '--': '{',
            '?`': '>',
            '``': '\\',
            'fi': '\x0c',
            'ff': '\x0b',
            'fl': '\r',
            '{-': '|',
            }
        self.param_count = 7
        self.parc_face_byte = 10
        self.seven_bit_safe = False

        def _tag(k):
            if k is None:
                return 0 # vanilla
            else:
                return 1 # kerned

        def _remainder(k):
            if k is None:
                return 0
            else:
                return k

        self.char_table = dict([
            (codepoint,
            CharacterMetric(
                codepoint,
                w, h, d, ital,
                _tag(k), _remainder(k),
                parent = self,
                )) for codepoint, w, h, d, ital, k in [
                    # c   w   h   d ital  kern
                    [  0, 18, 12,  0,  0, None],
                    [  1, 30, 12,  0,  0, None],
                    [  2, 28, 12,  0,  0, None],
                    [  3, 22, 12,  0,  0, None],
                    [  4, 20, 12,  0,  0, None],
                    [  5, 26, 12,  0,  0, None],
                    [  6, 24, 12,  0,  0, None],
                    [  7, 28, 12,  0,  0, None],
                    [  8, 24, 12,  0,  0, None],
                    [  9, 28, 12,  0,  0, None],
                    [ 10, 24, 12,  0,  0, None],
                    [ 11, 16, 13,  0,  4, 10],
                    [ 12, 15, 13,  0,  0, None],
                    [ 13, 15, 13,  0,  0, None],
                    [ 14, 30, 13,  0,  0, None],
                    [ 15, 30, 13,  0,  0, None],
                    [ 16,  1,  3,  0,  0, None],
                    [ 17,  2,  3,  8,  0, None],
                    [ 18, 10, 13,  0,  0, None],
                    [ 19, 10, 13,  0,  0, None],
                    [ 20, 10,  9,  0,  0, None],
                    [ 21, 10, 13,  0,  0, None],
                    [ 22, 10,  6,  0,  0, None],
                    [ 23, 26, 13,  0,  0, None],
                    [ 24,  8,  0,  6,  0, None],
                    [ 25, 11, 13,  0,  0, None],
                    [ 26, 24,  3,  0,  0, None],
                    [ 27, 28,  3,  0,  0, None],
                    [ 28, 10,  5,  5,  0, None],
                    [ 29, 31, 12,  0,  0, None],
                    [ 30, 34, 12,  0,  0, None],
                    [ 31, 28, 14,  2,  0, None],
                    [ 32,  1,  3,  0,  0, 0],
                    [ 33,  1, 13,  0,  0, 23],
                    [ 34, 10, 13,  0,  0, None],
                    [ 35, 30, 13,  7,  0, None],
                    [ 36, 10, 15,  3,  0, None],
                    [ 37, 30, 15,  3,  0, None],
                    [ 38, 28, 13,  0,  0, None],
                    [ 39,  1, 13,  0,  0, 18],
                    [ 40,  5, 15,  9,  0, None],
                    [ 41,  5, 15,  9,  0, None],
                    [ 42, 10, 15,  0,  0, None],
                    [ 43, 28,  7,  4,  0, None],
                    [ 44,  1,  1,  8,  0, None],
                    [ 45,  3,  3,  0,  0, 21],
                    [ 46,  1,  1,  0,  0, None],
                    [ 47, 10, 15,  9,  0, None],
                    [ 48, 10, 10,  0,  0, None],
                    [ 49, 10, 10,  0,  0, None],
                    [ 50, 10, 10,  0,  0, None],
                    [ 51, 10, 10,  0,  0, None],
                    [ 52, 10, 10,  0,  0, None],
                    [ 53, 10, 10,  0,  0, None],
                    [ 54, 10, 10,  0,  0, None],
                    [ 55, 10, 10,  0,  0, None],
                    [ 56, 10, 10,  0,  0, None],
                    [ 57, 10, 10,  0,  0, None],
                    [ 58,  1,  3,  0,  0, None],
                    [ 59,  1,  3,  8,  0, None],
                    [ 60,  1,  4,  8,  0, None],
                    [ 61, 28,  2,  1,  0, None],
                    [ 62,  9,  4,  8,  0, None],
                    [ 63,  9, 13,  0,  0, 24],
                    [ 64, 28, 13,  0,  0, None],
                    [ 65, 26, 12,  0,  0, 76],
                    [ 66, 23, 12,  0,  0, None],
                    [ 67, 24, 12,  0,  0, None],
                    [ 68, 27, 12,  0,  0, 53],
                    [ 69, 21, 12,  0,  0, None],
                    [ 70, 19, 12,  0,  0, 36],
                    [ 71, 29, 12,  0,  0, None],
                    [ 72, 26, 12,  0,  0, None],
                    [ 73,  4, 12,  0,  0, 87],
                    [ 74, 12, 12,  0,  0, None],
                    [ 75, 28, 12,  0,  0, 42],
                    [ 76, 18, 12,  0,  0, 82],
                    [ 77, 32, 12,  0,  0, None],
                    [ 78, 26, 12,  0,  0, None],
                    [ 79, 28, 12,  0,  0, 53],
                    [ 80, 21, 12,  0,  0, 30],
                    [ 81, 28, 12,  8,  0, None],
                    [ 82, 25, 12,  0,  0, 76],
                    [ 83, 15, 12,  0,  0, None],
                    [ 84, 24, 12,  0,  0, 46],
                    [ 85, 26, 12,  0,  0, None],
                    [ 86, 26, 12,  0,  1, 36],
                    [ 87, 35, 12,  0,  1, 36],
                    [ 88, 26, 12,  0,  0, 42],
                    [ 89, 26, 12,  0,  2, 47],
                    [ 90, 17, 12,  0,  0, None],
                    [ 91,  1, 15,  9,  0, None],
                    [ 92, 10, 13,  0,  0, None],
                    [ 93,  1, 15,  9,  0, None],
                    [ 94, 10, 13,  0,  0, None],
                    [ 95,  1, 11,  0,  0, None],
                    [ 96,  1, 13,  0,  0, 17],
                    [ 97, 10,  3,  0,  0, 72],
                    [ 98, 15, 13,  0,  0, 66],
                    [ 99,  8,  3,  0,  0, 64],
                    [100, 15, 13,  0,  0, None],
                    [101,  8,  3,  0,  0, None],
                    [102,  2, 13,  0,  4, 2],
                    [103, 10,  3,  8,  1, 86],
                    [104, 15, 13,  0,  0, 58],
                    [105,  1, 11,  0,  0, None],
                    [106,  2, 11,  8,  0, None],
                    [107, 14, 13,  0,  0, 25],
                    [108,  1, 13,  0,  0, None],
                    [109, 30,  3,  0,  0, 58],
                    [110, 15,  3,  0,  0, 58],
                    [111, 10,  3,  0,  0, 66],
                    [112, 15,  3,  8,  0, 66],
                    [113, 13,  3,  8,  0, None],
                    [114,  6,  3,  0,  0, None],
                    [115,  7,  3,  0,  0, None],
                    [116,  5,  8,  0,  0, 74],
                    [117, 15,  3,  0,  0, 75],
                    [118, 14,  3,  0,  1, 25],
                    [119, 24,  3,  0,  1, 26],
                    [120, 14,  3,  0,  0, None],
                    [121, 14,  3,  8,  1, 31],
                    [122,  8,  3,  0,  0, None],
                    [123, 10,  3,  0,  3, 22],
                    [124, 33,  3,  0,  3, None],
                    [125, 10, 13,  0,  0, None],
                    [126, 10, 11,  0,  0, None],
                    [127, 10, 11,  0,  0, None],
                  ]])

        self.kerns = {
          "\x0b'" : yex.value.Dimen(50973, 'sp'),
          '\x0b?' : yex.value.Dimen(50973, 'sp'),
          '\x0b!' : yex.value.Dimen(50973, 'sp'),
          '\x0b)' : yex.value.Dimen(50973, 'sp'),
          '\x0b]' : yex.value.Dimen(50973, 'sp'),
          ' l'    : yex.value.Dimen(-182045, 'sp'),
          ' L'    : yex.value.Dimen(-209352, 'sp'),
          "'?"    : yex.value.Dimen(72818, 'sp'),
          "'!"    : yex.value.Dimen(72818, 'sp'),
          'At'    : yex.value.Dimen(-18205, 'sp'),
          'AC'    : yex.value.Dimen(-18205, 'sp'),
          'AO'    : yex.value.Dimen(-18205, 'sp'),
          'AG'    : yex.value.Dimen(-18205, 'sp'),
          'AU'    : yex.value.Dimen(-18205, 'sp'),
          'AQ'    : yex.value.Dimen(-18205, 'sp'),
          'AT'    : yex.value.Dimen(-54614, 'sp'),
          'AY'    : yex.value.Dimen(-54614, 'sp'),
          'AV'    : yex.value.Dimen(-72819, 'sp'),
          'AW'    : yex.value.Dimen(-72819, 'sp'),
          'DX'    : yex.value.Dimen(-18205, 'sp'),
          'DW'    : yex.value.Dimen(-18205, 'sp'),
          'DA'    : yex.value.Dimen(-18205, 'sp'),
          'DV'    : yex.value.Dimen(-18205, 'sp'),
          'DY'    : yex.value.Dimen(-18205, 'sp'),
          'Fo'    : yex.value.Dimen(-54614, 'sp'),
          'Fe'    : yex.value.Dimen(-54614, 'sp'),
          'Fu'    : yex.value.Dimen(-54614, 'sp'),
          'Fr'    : yex.value.Dimen(-54614, 'sp'),
          'Fa'    : yex.value.Dimen(-54614, 'sp'),
          'FA'    : yex.value.Dimen(-72819, 'sp'),
          'FO'    : yex.value.Dimen(-18205, 'sp'),
          'FC'    : yex.value.Dimen(-18205, 'sp'),
          'FG'    : yex.value.Dimen(-18205, 'sp'),
          'FQ'    : yex.value.Dimen(-18205, 'sp'),
          'II'    : yex.value.Dimen(18205, 'sp'),
          'KO'    : yex.value.Dimen(-18205, 'sp'),
          'KC'    : yex.value.Dimen(-18205, 'sp'),
          'KG'    : yex.value.Dimen(-18205, 'sp'),
          'KQ'    : yex.value.Dimen(-18205, 'sp'),
          'LT'    : yex.value.Dimen(-54614, 'sp'),
          'LY'    : yex.value.Dimen(-54614, 'sp'),
          'LV'    : yex.value.Dimen(-72819, 'sp'),
          'LW'    : yex.value.Dimen(-72819, 'sp'),
          'OX'    : yex.value.Dimen(-18205, 'sp'),
          'OW'    : yex.value.Dimen(-18205, 'sp'),
          'OA'    : yex.value.Dimen(-18205, 'sp'),
          'OV'    : yex.value.Dimen(-18205, 'sp'),
          'OY'    : yex.value.Dimen(-18205, 'sp'),
          'PA'    : yex.value.Dimen(-54614, 'sp'),
          'Po'    : yex.value.Dimen(-18205, 'sp'),
          'Pe'    : yex.value.Dimen(-18205, 'sp'),
          'Pa'    : yex.value.Dimen(-18205, 'sp'),
          'P.'    : yex.value.Dimen(-54614, 'sp'),
          'P,'    : yex.value.Dimen(-54614, 'sp'),
          'Rt'    : yex.value.Dimen(-18205, 'sp'),
          'RC'    : yex.value.Dimen(-18205, 'sp'),
          'RO'    : yex.value.Dimen(-18205, 'sp'),
          'RG'    : yex.value.Dimen(-18205, 'sp'),
          'RU'    : yex.value.Dimen(-18205, 'sp'),
          'RQ'    : yex.value.Dimen(-18205, 'sp'),
          'RT'    : yex.value.Dimen(-54614, 'sp'),
          'RY'    : yex.value.Dimen(-54614, 'sp'),
          'RV'    : yex.value.Dimen(-72819, 'sp'),
          'RW'    : yex.value.Dimen(-72819, 'sp'),
          'Ty'    : yex.value.Dimen(-18205, 'sp'),
          'Te'    : yex.value.Dimen(-54614, 'sp'),
          'To'    : yex.value.Dimen(-54614, 'sp'),
          'Tr'    : yex.value.Dimen(-54614, 'sp'),
          'Ta'    : yex.value.Dimen(-54614, 'sp'),
          'TA'    : yex.value.Dimen(-54614, 'sp'),
          'Tu'    : yex.value.Dimen(-54614, 'sp'),
          'Vo'    : yex.value.Dimen(-54614, 'sp'),
          'Ve'    : yex.value.Dimen(-54614, 'sp'),
          'Vu'    : yex.value.Dimen(-54614, 'sp'),
          'Vr'    : yex.value.Dimen(-54614, 'sp'),
          'Va'    : yex.value.Dimen(-54614, 'sp'),
          'VA'    : yex.value.Dimen(-72819, 'sp'),
          'VO'    : yex.value.Dimen(-18205, 'sp'),
          'VC'    : yex.value.Dimen(-18205, 'sp'),
          'VG'    : yex.value.Dimen(-18205, 'sp'),
          'VQ'    : yex.value.Dimen(-18205, 'sp'),
          'Wo'    : yex.value.Dimen(-54614, 'sp'),
          'We'    : yex.value.Dimen(-54614, 'sp'),
          'Wu'    : yex.value.Dimen(-54614, 'sp'),
          'Wr'    : yex.value.Dimen(-54614, 'sp'),
          'Wa'    : yex.value.Dimen(-54614, 'sp'),
          'WA'    : yex.value.Dimen(-72819, 'sp'),
          'WO'    : yex.value.Dimen(-18205, 'sp'),
          'WC'    : yex.value.Dimen(-18205, 'sp'),
          'WG'    : yex.value.Dimen(-18205, 'sp'),
          'WQ'    : yex.value.Dimen(-18205, 'sp'),
          'XO'    : yex.value.Dimen(-18205, 'sp'),
          'XC'    : yex.value.Dimen(-18205, 'sp'),
          'XG'    : yex.value.Dimen(-18205, 'sp'),
          'XQ'    : yex.value.Dimen(-18205, 'sp'),
          'Ye'    : yex.value.Dimen(-54614, 'sp'),
          'Yo'    : yex.value.Dimen(-54614, 'sp'),
          'Yr'    : yex.value.Dimen(-54614, 'sp'),
          'Ya'    : yex.value.Dimen(-54614, 'sp'),
          'YA'    : yex.value.Dimen(-54614, 'sp'),
          'Yu'    : yex.value.Dimen(-54614, 'sp'),
          'av'    : yex.value.Dimen(-18205, 'sp'),
          'aj'    : yex.value.Dimen(36408, 'sp'),
          'ay'    : yex.value.Dimen(-18205, 'sp'),
          'aw'    : yex.value.Dimen(-18205, 'sp'),
          'be'    : yex.value.Dimen(18205, 'sp'),
          'bo'    : yex.value.Dimen(18205, 'sp'),
          'bx'    : yex.value.Dimen(-18205, 'sp'),
          'bd'    : yex.value.Dimen(18205, 'sp'),
          'bc'    : yex.value.Dimen(18205, 'sp'),
          'bq'    : yex.value.Dimen(18205, 'sp'),
          'bv'    : yex.value.Dimen(-18205, 'sp'),
          'bj'    : yex.value.Dimen(36408, 'sp'),
          'by'    : yex.value.Dimen(-18205, 'sp'),
          'bw'    : yex.value.Dimen(-18205, 'sp'),
          'ch'    : yex.value.Dimen(-18205, 'sp'),
          'ck'    : yex.value.Dimen(-18205, 'sp'),
          "f'"    : yex.value.Dimen(50973, 'sp'),
          'f?'    : yex.value.Dimen(50973, 'sp'),
          'f!'    : yex.value.Dimen(50973, 'sp'),
          'f)'    : yex.value.Dimen(50973, 'sp'),
          'f]'    : yex.value.Dimen(50973, 'sp'),
          'gj'    : yex.value.Dimen(18205, 'sp'),
          'ht'    : yex.value.Dimen(-18205, 'sp'),
          'hu'    : yex.value.Dimen(-18205, 'sp'),
          'hb'    : yex.value.Dimen(-18205, 'sp'),
          'hy'    : yex.value.Dimen(-18205, 'sp'),
          'hv'    : yex.value.Dimen(-18205, 'sp'),
          'hw'    : yex.value.Dimen(-18205, 'sp'),
          'ka'    : yex.value.Dimen(-18205, 'sp'),
          'ke'    : yex.value.Dimen(-18205, 'sp'),
          'ko'    : yex.value.Dimen(-18205, 'sp'),
          'kc'    : yex.value.Dimen(-18205, 'sp'),
          'mt'    : yex.value.Dimen(-18205, 'sp'),
          'mu'    : yex.value.Dimen(-18205, 'sp'),
          'mb'    : yex.value.Dimen(-18205, 'sp'),
          'my'    : yex.value.Dimen(-18205, 'sp'),
          'mv'    : yex.value.Dimen(-18205, 'sp'),
          'mw'    : yex.value.Dimen(-18205, 'sp'),
          'nt'    : yex.value.Dimen(-18205, 'sp'),
          'nu'    : yex.value.Dimen(-18205, 'sp'),
          'nb'    : yex.value.Dimen(-18205, 'sp'),
          'ny'    : yex.value.Dimen(-18205, 'sp'),
          'nv'    : yex.value.Dimen(-18205, 'sp'),
          'nw'    : yex.value.Dimen(-18205, 'sp'),
          'oe'    : yex.value.Dimen(18205, 'sp'),
          'oo'    : yex.value.Dimen(18205, 'sp'),
          'ox'    : yex.value.Dimen(-18205, 'sp'),
          'od'    : yex.value.Dimen(18205, 'sp'),
          'oc'    : yex.value.Dimen(18205, 'sp'),
          'oq'    : yex.value.Dimen(18205, 'sp'),
          'ov'    : yex.value.Dimen(-18205, 'sp'),
          'oj'    : yex.value.Dimen(36408, 'sp'),
          'oy'    : yex.value.Dimen(-18205, 'sp'),
          'ow'    : yex.value.Dimen(-18205, 'sp'),
          'pe'    : yex.value.Dimen(18205, 'sp'),
          'po'    : yex.value.Dimen(18205, 'sp'),
          'px'    : yex.value.Dimen(-18205, 'sp'),
          'pd'    : yex.value.Dimen(18205, 'sp'),
          'pc'    : yex.value.Dimen(18205, 'sp'),
          'pq'    : yex.value.Dimen(18205, 'sp'),
          'pv'    : yex.value.Dimen(-18205, 'sp'),
          'pj'    : yex.value.Dimen(36408, 'sp'),
          'py'    : yex.value.Dimen(-18205, 'sp'),
          'pw'    : yex.value.Dimen(-18205, 'sp'),
          'ty'    : yex.value.Dimen(-18205, 'sp'),
          'tw'    : yex.value.Dimen(-18205, 'sp'),
          'uw'    : yex.value.Dimen(-18205, 'sp'),
          'va'    : yex.value.Dimen(-18205, 'sp'),
          've'    : yex.value.Dimen(-18205, 'sp'),
          'vo'    : yex.value.Dimen(-18205, 'sp'),
          'vc'    : yex.value.Dimen(-18205, 'sp'),
          'we'    : yex.value.Dimen(-18205, 'sp'),
          'wa'    : yex.value.Dimen(-18205, 'sp'),
          'wo'    : yex.value.Dimen(-18205, 'sp'),
          'wc'    : yex.value.Dimen(-18205, 'sp'),
          'yo'    : yex.value.Dimen(-18205, 'sp'),
          'ye'    : yex.value.Dimen(-18205, 'sp'),
          'ya'    : yex.value.Dimen(-18205, 'sp'),
          'y.'    : yex.value.Dimen(-54614, 'sp'),
          'y,'    : yex.value.Dimen(-54614, 'sp'),
        }

        self.dimens = {
          1       : 0.0,
          2       : yex.value.Dimen(218453, 'sp'),
          3       : yex.value.Dimen(109226, 'sp'),
          4       : yex.value.Dimen(72818, 'sp'),
          5       : yex.value.Dimen(282168, 'sp'),
          6       : yex.value.Dimen(655361, 'sp'),
          7       : yex.value.Dimen(72818, 'sp'),
        }

        self.height_table = [
         yex.value.Dimen(0, 'sp'),
         yex.value.Dimen(69176, 'sp'),
         yex.value.Dimen(240435, 'sp'),
         yex.value.Dimen(282168, 'sp'),
         yex.value.Dimen(327680, 'sp'),
         yex.value.Dimen(345885, 'sp'),
         yex.value.Dimen(372098, 'sp'),
         yex.value.Dimen(382293, 'sp'),
         yex.value.Dimen(403098, 'sp'),
         yex.value.Dimen(411876, 'sp'),
         yex.value.Dimen(422343, 'sp'),
         yex.value.Dimen(437688, 'sp'),
         yex.value.Dimen(447828, 'sp'),
         yex.value.Dimen(455111, 'sp'),
         yex.value.Dimen(479686, 'sp'),
         yex.value.Dimen(491520, 'sp'),
        ]

        self.width_table = [
         yex.value.Dimen(0, 'sp'),
         yex.value.Dimen(182045, 'sp'),
         yex.value.Dimen(200250, 'sp'),
         yex.value.Dimen(218453, 'sp'),
         yex.value.Dimen(236658, 'sp'),
         yex.value.Dimen(254863, 'sp'),
         yex.value.Dimen(256683, 'sp'),
         yex.value.Dimen(258503, 'sp'),
         yex.value.Dimen(291271, 'sp'),
         yex.value.Dimen(309476, 'sp'),
         yex.value.Dimen(327681, 'sp'),
         yex.value.Dimen(327681, 'sp'),
         yex.value.Dimen(336783, 'sp'),
         yex.value.Dimen(345885, 'sp'),
         yex.value.Dimen(345886, 'sp'),
         yex.value.Dimen(364090, 'sp'),
         yex.value.Dimen(382295, 'sp'),
         yex.value.Dimen(400498, 'sp'),
         yex.value.Dimen(409601, 'sp'),
         yex.value.Dimen(427806, 'sp'),
         yex.value.Dimen(436908, 'sp'),
         yex.value.Dimen(446010, 'sp'),
         yex.value.Dimen(455111, 'sp'),
         yex.value.Dimen(464215, 'sp'),
         yex.value.Dimen(473316, 'sp'),
         yex.value.Dimen(482418, 'sp'),
         yex.value.Dimen(491521, 'sp'),
         yex.value.Dimen(500623, 'sp'),
         yex.value.Dimen(509726, 'sp'),
         yex.value.Dimen(514276, 'sp'),
         yex.value.Dimen(546135, 'sp'),
         yex.value.Dimen(591646, 'sp'),
         yex.value.Dimen(600748, 'sp'),
         yex.value.Dimen(655361, 'sp'),
         yex.value.Dimen(664463, 'sp'),
         yex.value.Dimen(673566, 'sp'),
        ]

        self.depth_table = [
         yex.value.Dimen(0, 'sp'),
         yex.value.Dimen(-87245, 'sp'),
         yex.value.Dimen(31858, 'sp'),
         yex.value.Dimen(36408, 'sp'),
         yex.value.Dimen(54613, 'sp'),
         yex.value.Dimen(63716, 'sp'),
         yex.value.Dimen(111501, 'sp'),
         yex.value.Dimen(127430, 'sp'),
         yex.value.Dimen(127431, 'sp'),
         yex.value.Dimen(163840, 'sp'),
        ]

        self.italic_correction_table = [
         yex.value.Dimen(0, 'sp'),
         yex.value.Dimen(9101, 'sp'),
         yex.value.Dimen(16383, 'sp'),
         yex.value.Dimen(18205, 'sp'),
         yex.value.Dimen(50973, 'sp'),
        ]

    def get_character(self, code):
        return self.char_table.get(code)

############################################################################

def dump_font(name):

    def reconstruct(v):

        def recursed(opener, closer, items, associative=False):
            indent = ' ' * 8
            result = opener+'\n'
            for item in items:
                result += indent
                if associative:
                    result += reconstruct(item[0]) + ': '
                    result += reconstruct(item[1]) + ',\n'
                else:
                    result += reconstruct(item) + ',\n'

            result += indent + closer
            return result

        if isinstance(v, (float, int, str, bytes)) or v is None:
            return repr(v)
        elif isinstance(v, (set)):
            if len(v)==0:
                return 'set()'
            else:
                return recursed('{', '}', sorted(list(v)))
        elif isinstance(v, (list)):
            return recursed('{', '}', v)
        elif isinstance(v, (dict)):
            return recursed('{', '}', v.items(), associative=True)
        elif isinstance(v, (set, list, dict)):
            print(v, type(v))
            assert len(v)==0 # otherwise we'll need to recurse
            return repr(v)
        elif isinstance(v, yex.value.Dimen):
            return f"yex.value.Dimen({v.value}, 'sp')"
        else:
            raise TypeError(type(v))

    def dump_object(thing,
            hide_fields):
        fields = [x for x in dir(thing) if
                not x.startswith('_')
                and x==x.lower()
                and '_table' not in x
                and not x in hide_fields
                ]

        items = dict([(x, getattr(thing,x)) for x in fields
            if not hasattr(getattr(thing,x),'__call__')])

        for f, v in items.items():
            print('    self.%s = %s' % (
                f,
                reconstruct(v),
                ))

        print()

    def dump_dimens_table(name, t):

        print(f'    self.{name} = {{')
        for f,v in t.items():
            print('      %-8s: %s,' % (
                repr(f), reconstruct(v),
                ))
        print('    }')
        print()

    def dump_ints_list(name, t):
        print(f'    self.{name}_table = [')
        for v in t:
            print('     %s,' % (
                reconstruct(v),
                ))
        print('    ]')
        print()

    def dump_char_table(d):
        print('    self.char_table = [')
        print('      # c   w   h   d ital  kern')
        for codepoint, m in d.items():

            if m.tag=='vanilla':
                kern = None
            elif m.tag=='kerned':
                kern = m.remainder
            else:
                raise ValueError(f"please implement tag={m.tag}")

            print(
                '      [%3d, %2d, %2d, %2d, %2d, %s],' % (
                    codepoint, m.width_idx, m.height_idx,
                    m.depth_idx, m.char_ic_idx,
                    reconstruct(kern),
                ))
        print('    ]')
        print()


    fn = Filename(name).resolve()

    with open(fn, 'rb') as f:
        font = Tfm(f=f)

    print(f'    # Definition of {name}')
    dump_object(font,
            hide_fields=['glyphs', 'metrics', 'f', 'filename'],
            )

    print('    # metrics')
    dump_object(font.metrics,
            hide_fields=['kerns', 'dimens'],
            )

    print('    # tables')

    dump_char_table(font.metrics.char_table)

    dump_dimens_table('kerns', font.metrics.kerns)
    dump_dimens_table('dimens', font.metrics.dimens)

    for length in ['height', 'width', 'depth', 'italic_correction']:
        dump_ints_list(
                length,
                getattr(font.metrics, f'{length}_table'),
                )

if __name__=='__main__':
    dump_font('cmr10.tfm')
