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
        self.filename = Filename('cmr10.tfm')
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
          "\x0b'" : 5097,
          '\x0b?' : 5097,
          '\x0b!' : 5097,
          '\x0b)' : 5097,
          '\x0b]' : 5097,
          ' l'    : -18204,
          ' L'    : -20935,
          "'?"    : 7281,
          "'!"    : 7281,
          'At'    : -1820,
          'AC'    : -1820,
          'AO'    : -1820,
          'AG'    : -1820,
          'AU'    : -1820,
          'AQ'    : -1820,
          'AT'    : -5461,
          'AY'    : -5461,
          'AV'    : -7281,
          'AW'    : -7281,
          'DX'    : -1820,
          'DW'    : -1820,
          'DA'    : -1820,
          'DV'    : -1820,
          'DY'    : -1820,
          'Fo'    : -5461,
          'Fe'    : -5461,
          'Fu'    : -5461,
          'Fr'    : -5461,
          'Fa'    : -5461,
          'FA'    : -7281,
          'FO'    : -1820,
          'FC'    : -1820,
          'FG'    : -1820,
          'FQ'    : -1820,
          'II'    : 1820,
          'KO'    : -1820,
          'KC'    : -1820,
          'KG'    : -1820,
          'KQ'    : -1820,
          'LT'    : -5461,
          'LY'    : -5461,
          'LV'    : -7281,
          'LW'    : -7281,
          'OX'    : -1820,
          'OW'    : -1820,
          'OA'    : -1820,
          'OV'    : -1820,
          'OY'    : -1820,
          'PA'    : -5461,
          'Po'    : -1820,
          'Pe'    : -1820,
          'Pa'    : -1820,
          'P.'    : -5461,
          'P,'    : -5461,
          'Rt'    : -1820,
          'RC'    : -1820,
          'RO'    : -1820,
          'RG'    : -1820,
          'RU'    : -1820,
          'RQ'    : -1820,
          'RT'    : -5461,
          'RY'    : -5461,
          'RV'    : -7281,
          'RW'    : -7281,
          'Ty'    : -1820,
          'Te'    : -5461,
          'To'    : -5461,
          'Tr'    : -5461,
          'Ta'    : -5461,
          'TA'    : -5461,
          'Tu'    : -5461,
          'Vo'    : -5461,
          'Ve'    : -5461,
          'Vu'    : -5461,
          'Vr'    : -5461,
          'Va'    : -5461,
          'VA'    : -7281,
          'VO'    : -1820,
          'VC'    : -1820,
          'VG'    : -1820,
          'VQ'    : -1820,
          'Wo'    : -5461,
          'We'    : -5461,
          'Wu'    : -5461,
          'Wr'    : -5461,
          'Wa'    : -5461,
          'WA'    : -7281,
          'WO'    : -1820,
          'WC'    : -1820,
          'WG'    : -1820,
          'WQ'    : -1820,
          'XO'    : -1820,
          'XC'    : -1820,
          'XG'    : -1820,
          'XQ'    : -1820,
          'Ye'    : -5461,
          'Yo'    : -5461,
          'Yr'    : -5461,
          'Ya'    : -5461,
          'YA'    : -5461,
          'Yu'    : -5461,
          'av'    : -1820,
          'aj'    : 3640,
          'ay'    : -1820,
          'aw'    : -1820,
          'be'    : 1820,
          'bo'    : 1820,
          'bx'    : -1820,
          'bd'    : 1820,
          'bc'    : 1820,
          'bq'    : 1820,
          'bv'    : -1820,
          'bj'    : 3640,
          'by'    : -1820,
          'bw'    : -1820,
          'ch'    : -1820,
          'ck'    : -1820,
          "f'"    : 5097,
          'f?'    : 5097,
          'f!'    : 5097,
          'f)'    : 5097,
          'f]'    : 5097,
          'gj'    : 1820,
          'ht'    : -1820,
          'hu'    : -1820,
          'hb'    : -1820,
          'hy'    : -1820,
          'hv'    : -1820,
          'hw'    : -1820,
          'ka'    : -1820,
          'ke'    : -1820,
          'ko'    : -1820,
          'kc'    : -1820,
          'mt'    : -1820,
          'mu'    : -1820,
          'mb'    : -1820,
          'my'    : -1820,
          'mv'    : -1820,
          'mw'    : -1820,
          'nt'    : -1820,
          'nu'    : -1820,
          'nb'    : -1820,
          'ny'    : -1820,
          'nv'    : -1820,
          'nw'    : -1820,
          'oe'    : 1820,
          'oo'    : 1820,
          'ox'    : -1820,
          'od'    : 1820,
          'oc'    : 1820,
          'oq'    : 1820,
          'ov'    : -1820,
          'oj'    : 3640,
          'oy'    : -1820,
          'ow'    : -1820,
          'pe'    : 1820,
          'po'    : 1820,
          'px'    : -1820,
          'pd'    : 1820,
          'pc'    : 1820,
          'pq'    : 1820,
          'pv'    : -1820,
          'pj'    : 3640,
          'py'    : -1820,
          'pw'    : -1820,
          'ty'    : -1820,
          'tw'    : -1820,
          'uw'    : -1820,
          'va'    : -1820,
          've'    : -1820,
          'vo'    : -1820,
          'vc'    : -1820,
          'we'    : -1820,
          'wa'    : -1820,
          'wo'    : -1820,
          'wc'    : -1820,
          'yo'    : -1820,
          'ye'    : -1820,
          'ya'    : -1820,
          'y.'    : -5461,
          'y,'    : -5461,
        }

        self.dimens = {
          1       : 0,
          2       : 21845,
          3       : 10922,
          4       : 7281,
          5       : 28216,
          6       : 65536,
          7       : 7281,
        }

        self.height_table = [
         0,
         6917,
         24043,
         28216,
         32768,
         34588,
         37209,
         38229,
         40309,
         41187,
         42234,
         43768,
         44782,
         45511,
         47968,
         49152,
        ]

        self.width_table = [
         0,
         18204,
         20025,
         21845,
         23665,
         25486,
         25668,
         25850,
         29127,
         30947,
         32768,
         32768,
         33678,
         34588,
         34588,
         36409,
         38229,
         40049,
         40960,
         42780,
         43690,
         44601,
         45511,
         46421,
         47331,
         48241,
         49152,
         50062,
         50972,
         51427,
         54613,
         59164,
         60074,
         65536,
         66446,
         67356,
        ]

        self.depth_table = [
         0,
         -8724,
         3185,
         3640,
         5461,
         6371,
         11150,
         12743,
         12743,
         16384,
        ]

        self.italic_correction_table = [
         0,
         910,
         1638,
         1820,
         5097,
        ]

    def get_character(self, code):
        return self.char_table.get(code)

############################################################################

def dump_font(name):

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
                repr(v),
                ))

        print()

    def dump_dimens_table(name, t):
        print(f'    self.{name} = {{')
        for f,v in t.items():
            print('      %-8s: %s,' % (
                repr(f), v))
        print('    }')
        print()

    def dump_ints_list(name, t):
        print(f'    self.{name}_table = [')
        for v in t:
            print('     %s,' % (
                v,
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
                    kern,
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
