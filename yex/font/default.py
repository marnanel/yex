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
    get_font_from_name(None)
    ```

    If you do
    ```
    get_font_from_name("cmr10")
    ```
    you will still get the metrics for `cmr10`.

    At the end of this module, there is some code which loads the
    real `cmr10.fnt` and produces the values for this class.
    Its output will need some rearranging before it fits the actual code.
    """

    def __init__(self):
        self.filename = Filename('cmr10.tfm')
        self.hyphenchar = 45
        self.scale = None
        self.skewchar = -1
        self.used = set()
        self.metrics = DefaultMetrics()
        self._glyphs = None

    @property
    def name(self):
        return 'cmr10'

class DefaultMetrics:

    def __init__(self):
        self.character_coding_scheme = b'TeX text'
        self.checksum = 1274110073
        self.design_size = 10485760
        self.first_char = 0
        self.font_identifier = b'CMR'
        self.last_char = 127
        self.ligatures = {
                '\x0bi': '\x0e', '\x0bl': '\x0f', '!`': '<', "''": '"',
                '--': '{', '?`': '>', '``': '\\', 'fi': '\x0c',
                'ff': '\x0b', 'fl': '\r', '{-': '|'}
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
        "\x0b'" : Dimen(     0.778, 'pt'),
        '\x0b?' : Dimen(     0.778, 'pt'),
        '\x0b!' : Dimen(     0.778, 'pt'),
        '\x0b)' : Dimen(     0.778, 'pt'),
        '\x0b]' : Dimen(     0.778, 'pt'),
        ' l'    : Dimen(    -2.778, 'pt'),
        ' L'    : Dimen(    -3.194, 'pt'),
        "'?"    : Dimen(     1.111, 'pt'),
        "'!"    : Dimen(     1.111, 'pt'),
        'At'    : Dimen(    -0.278, 'pt'),
        'AC'    : Dimen(    -0.278, 'pt'),
        'AO'    : Dimen(    -0.278, 'pt'),
        'AG'    : Dimen(    -0.278, 'pt'),
        'AU'    : Dimen(    -0.278, 'pt'),
        'AQ'    : Dimen(    -0.278, 'pt'),
        'AT'    : Dimen(    -0.833, 'pt'),
        'AY'    : Dimen(    -0.833, 'pt'),
        'AV'    : Dimen(    -1.111, 'pt'),
        'AW'    : Dimen(    -1.111, 'pt'),
        'DX'    : Dimen(    -0.278, 'pt'),
        'DW'    : Dimen(    -0.278, 'pt'),
        'DA'    : Dimen(    -0.278, 'pt'),
        'DV'    : Dimen(    -0.278, 'pt'),
        'DY'    : Dimen(    -0.278, 'pt'),
        'Fo'    : Dimen(    -0.833, 'pt'),
        'Fe'    : Dimen(    -0.833, 'pt'),
        'Fu'    : Dimen(    -0.833, 'pt'),
        'Fr'    : Dimen(    -0.833, 'pt'),
        'Fa'    : Dimen(    -0.833, 'pt'),
        'FA'    : Dimen(    -1.111, 'pt'),
        'FO'    : Dimen(    -0.278, 'pt'),
        'FC'    : Dimen(    -0.278, 'pt'),
        'FG'    : Dimen(    -0.278, 'pt'),
        'FQ'    : Dimen(    -0.278, 'pt'),
        'II'    : Dimen(     0.278, 'pt'),
        'KO'    : Dimen(    -0.278, 'pt'),
        'KC'    : Dimen(    -0.278, 'pt'),
        'KG'    : Dimen(    -0.278, 'pt'),
        'KQ'    : Dimen(    -0.278, 'pt'),
        'LT'    : Dimen(    -0.833, 'pt'),
        'LY'    : Dimen(    -0.833, 'pt'),
        'LV'    : Dimen(    -1.111, 'pt'),
        'LW'    : Dimen(    -1.111, 'pt'),
        'OX'    : Dimen(    -0.278, 'pt'),
        'OW'    : Dimen(    -0.278, 'pt'),
        'OA'    : Dimen(    -0.278, 'pt'),
        'OV'    : Dimen(    -0.278, 'pt'),
        'OY'    : Dimen(    -0.278, 'pt'),
        'PA'    : Dimen(    -0.833, 'pt'),
        'Po'    : Dimen(    -0.278, 'pt'),
        'Pe'    : Dimen(    -0.278, 'pt'),
        'Pa'    : Dimen(    -0.278, 'pt'),
        'P.'    : Dimen(    -0.833, 'pt'),
        'P,'    : Dimen(    -0.833, 'pt'),
        'Rt'    : Dimen(    -0.278, 'pt'),
        'RC'    : Dimen(    -0.278, 'pt'),
        'RO'    : Dimen(    -0.278, 'pt'),
        'RG'    : Dimen(    -0.278, 'pt'),
        'RU'    : Dimen(    -0.278, 'pt'),
        'RQ'    : Dimen(    -0.278, 'pt'),
        'RT'    : Dimen(    -0.833, 'pt'),
        'RY'    : Dimen(    -0.833, 'pt'),
        'RV'    : Dimen(    -1.111, 'pt'),
        'RW'    : Dimen(    -1.111, 'pt'),
        'Ty'    : Dimen(    -0.278, 'pt'),
        'Te'    : Dimen(    -0.833, 'pt'),
        'To'    : Dimen(    -0.833, 'pt'),
        'Tr'    : Dimen(    -0.833, 'pt'),
        'Ta'    : Dimen(    -0.833, 'pt'),
        'TA'    : Dimen(    -0.833, 'pt'),
        'Tu'    : Dimen(    -0.833, 'pt'),
        'Vo'    : Dimen(    -0.833, 'pt'),
        'Ve'    : Dimen(    -0.833, 'pt'),
        'Vu'    : Dimen(    -0.833, 'pt'),
        'Vr'    : Dimen(    -0.833, 'pt'),
        'Va'    : Dimen(    -0.833, 'pt'),
        'VA'    : Dimen(    -1.111, 'pt'),
        'VO'    : Dimen(    -0.278, 'pt'),
        'VC'    : Dimen(    -0.278, 'pt'),
        'VG'    : Dimen(    -0.278, 'pt'),
        'VQ'    : Dimen(    -0.278, 'pt'),
        'Wo'    : Dimen(    -0.833, 'pt'),
        'We'    : Dimen(    -0.833, 'pt'),
        'Wu'    : Dimen(    -0.833, 'pt'),
        'Wr'    : Dimen(    -0.833, 'pt'),
        'Wa'    : Dimen(    -0.833, 'pt'),
        'WA'    : Dimen(    -1.111, 'pt'),
        'WO'    : Dimen(    -0.278, 'pt'),
        'WC'    : Dimen(    -0.278, 'pt'),
        'WG'    : Dimen(    -0.278, 'pt'),
        'WQ'    : Dimen(    -0.278, 'pt'),
        'XO'    : Dimen(    -0.278, 'pt'),
        'XC'    : Dimen(    -0.278, 'pt'),
        'XG'    : Dimen(    -0.278, 'pt'),
        'XQ'    : Dimen(    -0.278, 'pt'),
        'Ye'    : Dimen(    -0.833, 'pt'),
        'Yo'    : Dimen(    -0.833, 'pt'),
        'Yr'    : Dimen(    -0.833, 'pt'),
        'Ya'    : Dimen(    -0.833, 'pt'),
        'YA'    : Dimen(    -0.833, 'pt'),
        'Yu'    : Dimen(    -0.833, 'pt'),
        'av'    : Dimen(    -0.278, 'pt'),
        'aj'    : Dimen(     0.556, 'pt'),
        'ay'    : Dimen(    -0.278, 'pt'),
        'aw'    : Dimen(    -0.278, 'pt'),
        'be'    : Dimen(     0.278, 'pt'),
        'bo'    : Dimen(     0.278, 'pt'),
        'bx'    : Dimen(    -0.278, 'pt'),
        'bd'    : Dimen(     0.278, 'pt'),
        'bc'    : Dimen(     0.278, 'pt'),
        'bq'    : Dimen(     0.278, 'pt'),
        'bv'    : Dimen(    -0.278, 'pt'),
        'bj'    : Dimen(     0.556, 'pt'),
        'by'    : Dimen(    -0.278, 'pt'),
        'bw'    : Dimen(    -0.278, 'pt'),
        'ch'    : Dimen(    -0.278, 'pt'),
        'ck'    : Dimen(    -0.278, 'pt'),
        "f'"    : Dimen(     0.778, 'pt'),
        'f?'    : Dimen(     0.778, 'pt'),
        'f!'    : Dimen(     0.778, 'pt'),
        'f)'    : Dimen(     0.778, 'pt'),
        'f]'    : Dimen(     0.778, 'pt'),
        'gj'    : Dimen(     0.278, 'pt'),
        'ht'    : Dimen(    -0.278, 'pt'),
        'hu'    : Dimen(    -0.278, 'pt'),
        'hb'    : Dimen(    -0.278, 'pt'),
        'hy'    : Dimen(    -0.278, 'pt'),
        'hv'    : Dimen(    -0.278, 'pt'),
        'hw'    : Dimen(    -0.278, 'pt'),
        'ka'    : Dimen(    -0.278, 'pt'),
        'ke'    : Dimen(    -0.278, 'pt'),
        'ko'    : Dimen(    -0.278, 'pt'),
        'kc'    : Dimen(    -0.278, 'pt'),
        'mt'    : Dimen(    -0.278, 'pt'),
        'mu'    : Dimen(    -0.278, 'pt'),
        'mb'    : Dimen(    -0.278, 'pt'),
        'my'    : Dimen(    -0.278, 'pt'),
        'mv'    : Dimen(    -0.278, 'pt'),
        'mw'    : Dimen(    -0.278, 'pt'),
        'nt'    : Dimen(    -0.278, 'pt'),
        'nu'    : Dimen(    -0.278, 'pt'),
        'nb'    : Dimen(    -0.278, 'pt'),
        'ny'    : Dimen(    -0.278, 'pt'),
        'nv'    : Dimen(    -0.278, 'pt'),
        'nw'    : Dimen(    -0.278, 'pt'),
        'oe'    : Dimen(     0.278, 'pt'),
        'oo'    : Dimen(     0.278, 'pt'),
        'ox'    : Dimen(    -0.278, 'pt'),
        'od'    : Dimen(     0.278, 'pt'),
        'oc'    : Dimen(     0.278, 'pt'),
        'oq'    : Dimen(     0.278, 'pt'),
        'ov'    : Dimen(    -0.278, 'pt'),
        'oj'    : Dimen(     0.556, 'pt'),
        'oy'    : Dimen(    -0.278, 'pt'),
        'ow'    : Dimen(    -0.278, 'pt'),
        'pe'    : Dimen(     0.278, 'pt'),
        'po'    : Dimen(     0.278, 'pt'),
        'px'    : Dimen(    -0.278, 'pt'),
        'pd'    : Dimen(     0.278, 'pt'),
        'pc'    : Dimen(     0.278, 'pt'),
        'pq'    : Dimen(     0.278, 'pt'),
        'pv'    : Dimen(    -0.278, 'pt'),
        'pj'    : Dimen(     0.556, 'pt'),
        'py'    : Dimen(    -0.278, 'pt'),
        'pw'    : Dimen(    -0.278, 'pt'),
        'ty'    : Dimen(    -0.278, 'pt'),
        'tw'    : Dimen(    -0.278, 'pt'),
        'uw'    : Dimen(    -0.278, 'pt'),
        'va'    : Dimen(    -0.278, 'pt'),
        've'    : Dimen(    -0.278, 'pt'),
        'vo'    : Dimen(    -0.278, 'pt'),
        'vc'    : Dimen(    -0.278, 'pt'),
        'we'    : Dimen(    -0.278, 'pt'),
        'wa'    : Dimen(    -0.278, 'pt'),
        'wo'    : Dimen(    -0.278, 'pt'),
        'wc'    : Dimen(    -0.278, 'pt'),
        'yo'    : Dimen(    -0.278, 'pt'),
        'ye'    : Dimen(    -0.278, 'pt'),
        'ya'    : Dimen(    -0.278, 'pt'),
        'y.'    : Dimen(    -0.833, 'pt'),
        'y,'    : Dimen(    -0.833, 'pt'),
        }

        self.dimens = {
        1       : Dimen(     0.000, 'pt'),
        2       : Dimen(     3.333, 'pt'),
        3       : Dimen(     1.667, 'pt'),
        4       : Dimen(     1.111, 'pt'),
        5       : Dimen(     4.306, 'pt'),
        6       : Dimen(    10.000, 'pt'),
        7       : Dimen(     1.111, 'pt'),
        }

        self.height_table = [
                 0.000,
                 1.056,
                 3.669,
                 4.306,
                 5.000,
                 5.278,
                 5.678,
                 5.833,
                 6.151,
                 6.285,
                 6.444,
                 6.679,
                 6.833,
                 6.944,
                 7.319,
                 7.500,
        ]

        self.width_table = [
                 0.000,
                 2.778,
                 3.056,
                 3.333,
                 3.611,
                 3.889,
                 3.917,
                 3.944,
                 4.444,
                 4.722,
                 5.000,
                 5.000,
                 5.139,
                 5.278,
                 5.278,
                 5.556,
                 5.833,
                 6.111,
                 6.250,
                 6.528,
                 6.667,
                 6.806,
                 6.944,
                 7.083,
                 7.222,
                 7.361,
                 7.500,
                 7.639,
                 7.778,
                 7.847,
                 8.333,
                 9.028,
                 9.167,
                10.000,
                10.139,
                10.278,
        ]

        self.depth_table = [
                 0.000,
                -1.331,
                 0.486,
                 0.556,
                 0.833,
                 0.972,
                 1.701,
                 1.944,
                 1.944,
                 2.500,
        ]

        self.italic_correction_table = [
                 0.000,
                 0.139,
                 0.250,
                 0.278,
                 0.778,
        ]

    def get_character(self, code):
        return self.char_table.get(code)

############################################################################

def dump_font(name):
    from yex.filename import Filename

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
            if v.__class__.__name__=='Filename':
                v = str(v)

            print('  self.%s = %s' % (
                f,
                repr(v),
                ))

        print()

    def dimen_as_sp(d):
        dimen = Dimen(d, 'pt')
        return "Dimen(%10.3f, 'pt')" % (
                float(dimen),)

    def dump_dimens_table(name, t):
        # a table of Dimen values, not necessarily font.dimens
        print(f'  self.{name} = {{')
        for f,v in t.items():
            print('    %-8s: %s,' % (
                repr(f),
                dimen_as_sp(v)))
        print('  }')
        print()

    def dump_floats_list(name, t):
        print(f'  self.{name} = [')
        for v in t:
            print('   %15.3f,' % (
                v,
                ))
        print('  ]')
        print()

    def dump_metrics(x):
        for field in dir(metrics):

            if field.startswith('_'):
                continue

            if field in ('kerns', 'ligatures', 'lig_kern_program',
                    'height_table', 'width_table', 'depth_table',
                    'italic_correction_table', 'dimens',
                    'kern_table', # 'duns_table',
                    ):
                continue

            value = getattr(metrics, field)

            if hasattr(value, '__call__'):
                continue

            print(format_line(field, metrics))

        print()

    def dump_char_table(d):
        print('  self.char_table = [')
        print('    # c   w   h   d ital  kern')
        for codepoint, m in d.items():

            if m.tag=='vanilla':
                kern = None
            elif m.tag=='kerned':
                kern = m.remainder
            else:
                raise ValueError(f"please implement tag={m.tag}")

            print(
                '    [%3d, %2d, %2d, %2d, %2d, %s],' % (
                    codepoint, m.width_idx, m.height_idx,
                    m.depth_idx, m.char_ic_idx,
                    kern,
                ))
        print('  ]')
        print()

    fn = Filename(name)
    fn.resolve()

    font = Tfm(fn)

    print('  # font')
    dump_object(font,
            hide_fields=['glyphs', 'metrics'],
            )

    print('  # metrics')
    dump_object(font.metrics,
            hide_fields=['kerns', 'dimens'],
            )

    print('  # tables')

    dump_char_table(font.metrics.char_table)

    dump_dimens_table('kerns', font.metrics.kerns)
    dump_dimens_table('dimens', font.metrics.dimens)

    for length in ['height', 'width', 'depth', 'italic_correction']:
        dump_floats_list(
                length,
                getattr(font.metrics, f'{length}_table'),
                )

if __name__=='__main__':
    dump_font('fonts/cmr10.tfm')
