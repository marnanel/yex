from . import *
import yex.font
import yex.document
import yex.parse
import yex.value
import yex.exception
import pytest
import io

def test_get_font_from_name(yex_test_fs):
    font = yex.font.get_font_from_name('cmr10.tfm')
    assert font.filename == 'cmr10.tfm'
    assert font.name == 'cmr10'
    assert font.scale == None

def test_get_font_from_name_setting_scale_dimen(yex_test_fs):

    font = yex.font.get_font_from_name('cmr10.tfm')
    font.scale = yex.value.Dimen(12, "pt")

    assert font.filename == 'cmr10.tfm'
    assert font.name == 'cmr10'
    assert isinstance(font.scale, yex.value.Dimen)
    assert font.scale == yex.value.Dimen(12, "pt")

def test_get_font_from_name_setting_scale_number(yex_test_fs):

    font = yex.font.get_font_from_name('cmr10.tfm')
    font.scale = yex.value.Number(12)

    assert font.filename == 'cmr10.tfm'
    assert font.name == 'cmr10'
    assert isinstance(font.scale, yex.value.Number)
    assert font.scale == 12

def test_font_from_tokens(yex_test_fs):

    string = r"cmr10.tfm"

    with expander_on_string(string) as e:
        font = yex.font.get_font_from_tokens(e)

        assert font.filename == 'cmr10.tfm'
        assert font.name == 'cmr10'
        assert font.scale == None

def test_font_from_tokens_with_scale_dimen(yex_test_fs):

    string = r"cmr10.tfm at 12pt"

    with expander_on_string(string) as e:
        font = yex.font.get_font_from_tokens(e)

        assert font.filename == 'cmr10.tfm'
        assert font.name == 'cmr10'
        assert isinstance(font.scale, yex.value.Dimen)
        assert font.scale == yex.value.Dimen(12, "pt")

def test_font_from_tokens_with_scale_number(yex_test_fs):

    string = r"cmr10.tfm scaled 12"

    with expander_on_string(string) as e:
        font = yex.font.get_font_from_tokens(e)

        assert font.filename == 'cmr10.tfm'
        assert font.name == 'cmr10'
        assert isinstance(font.scale, yex.value.Number)
        assert font.scale == 12

def test_font_used(yex_test_fs):
    font = yex.font.get_font_from_name('cmr10.tfm')
    assert list(font.used)==[]
    font[102] = yex.value.Dimen(12)

    assert font['A'].glyph is not None
    assert list(font.used)==[ord('A')]

    with pytest.raises(yex.exception.YexError):
        font[103] = yex.value.Dimen(12)

def test_font_glyphs(yex_test_fs):

    for fontname in [
            'cmr10.tfm', None,
            ]:
        font = yex.font.get_font_from_name('cmr10.tfm')

        assert font['A'].glyph is not None, font

        found = '\n'.join(font['A'].glyph.ascii_art())
        expected = ENORMOUS_A
        assert found==expected, font

def test_font_glyph_image(yex_test_fs):
    font = yex.font.get_font_from_name('cmr10.tfm')
    a = font['A'].glyph.image
    enormous_A = ENORMOUS_A.split('\n')

    for y in range(a.height):
        for x in range(a.width):
            found = a.getpixel((x,y))[3]

            if enormous_A[y][x]=='X':
                expected = 255
            else:
                expected = 0

            assert found==expected, f"{x}, {y}"

def test_get_font_from_name(yex_test_fs):
    for name in [
            'cmr10',
            'cmr10.tfm',
            ]:
        font = yex.font.get_font_from_name(name)
        assert isinstance(font, yex.font.Tfm)

def test_font_identifier(yex_test_fs):

    cmr10 = yex.font.get_font_from_name('cmr10.tfm')
    assert cmr10.identifier == r'\cmr10'

    nullfont = yex.font.Nullfont()
    assert nullfont.identifier == r'\nullfont'

def test_default_font():

    default_font = yex.font.get_font_from_name(None)
    cmr10 = yex.font.get_font_from_name('fonts/cmr10.tfm')

    for field in [
            'name',
            'identifier',
            'hyphenchar',
            'skewchar',
            ]:
        assert getattr(default_font, field)==getattr(cmr10, field)

    tolerance = 0.001

    for codepoint in range(ord('a'), ord('z')+1):
        letter = chr(codepoint)

        dm = default_font[letter].metrics
        cm = cmr10[letter].metrics

        for field in ['height', 'width', 'depth', 'italic_correction']:
            assert (getattr(dm, field)-getattr(cm, field))<tolerance, letter

ENORMOUS_A = """
..........................XXX..........................
..........................XXX..........................
..........................XXX..........................
.........................XXXXX.........................
.........................XXXXX.........................
.........................XXXXX.........................
........................XXXXXXX........................
........................XXXXXXX........................
.......................XXXXXXXXX.......................
.......................XXXXXXXXX.......................
.......................XXXXXXXXX.......................
......................XXXXXXXXXXX......................
......................XX..XXXXXXX......................
......................XX..XXXXXXX......................
.....................XXX..XXXXXXXX.....................
.....................XX....XXXXXXX.....................
.....................XX....XXXXXXX.....................
....................XX.....XXXXXXXX....................
....................XX......XXXXXXX....................
....................XX......XXXXXXX....................
...................XX........XXXXXXX...................
...................XX........XXXXXXX...................
...................XX........XXXXXXX...................
..................XX..........XXXXXXX..................
..................XX..........XXXXXXX..................
..................XX..........XXXXXXX..................
.................XX............XXXXXXX.................
.................XX............XXXXXXX.................
.................XX............XXXXXXX.................
................XX..............XXXXXXX................
................XX..............XXXXXXX................
................XX..............XXXXXXX................
...............XX................XXXXXXX...............
...............XX................XXXXXXX...............
..............XXX................XXXXXXXX..............
..............XX..................XXXXXXX..............
..............XX..................XXXXXXX..............
.............XXXXXXXXXXXXXXXXXXXXXXXXXXXXX.............
.............XXXXXXXXXXXXXXXXXXXXXXXXXXXXX.............
.............XXXXXXXXXXXXXXXXXXXXXXXXXXXXX.............
............XXX....................XXXXXXXX............
............XX......................XXXXXXX............
............XX......................XXXXXXX............
...........XX.......................XXXXXXXX...........
...........XX........................XXXXXXX...........
...........XX........................XXXXXXX...........
..........XX..........................XXXXXXX..........
..........XX..........................XXXXXXX..........
..........XX..........................XXXXXXX..........
.........XX............................XXXXXXX.........
.........XX............................XXXXXXX.........
.........XX............................XXXXXXX.........
........XXX.............................XXXXXXX........
.......XXXX.............................XXXXXXX........
......XXXXXX............................XXXXXXXX.......
....XXXXXXXXXX........................XXXXXXXXXXX......
XXXXXXXXXXXXXXXXX................XXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXX................XXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXX................XXXXXXXXXXXXXXXXXXXXXX""".lstrip()
