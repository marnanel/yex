from test import *
import yex
import pytest
import io
import os
import unittest.mock
import logging

logger = logging.getLogger('yex.general')

def test_font_from_name(yex_test_fs):
    font = yex.font.Font.from_name('cmr10')
    assert isinstance(font, yex.font.Tfm)
    assert font.name == 'cmr10'
    assert font.scale == None

def test_font_from_name_setting_scale_dimen(yex_test_fs):

    font = yex.font.Font.from_name('cmr10')
    font.scale = yex.value.Dimen(12, "pt")

    assert font.name == 'cmr10'
    assert isinstance(font.scale, yex.value.Dimen)
    assert font.scale == yex.value.Dimen(12, "pt")

def test_font_from_name_setting_scale_number(yex_test_fs):

    font = yex.font.Font.from_name('cmr10')
    font.scale = yex.value.Number(12)

    assert font.name == 'cmr10'
    assert isinstance(font.scale, yex.value.Number)
    assert font.scale == 12

def test_font_from_tokens(yex_test_fs):

    string = r"cmr10"

    with expander_on_string(string) as e:
        font = yex.font.Font.from_tokens(e)

        assert font.name == 'cmr10'
        assert font.scale == None

def test_font_from_tokens_with_scale_dimen(yex_test_fs):

    string = r"cmr10 at 12pt"

    with expander_on_string(string) as e:
        font = yex.font.Font.from_tokens(e)

        assert font.name == 'cmr10'
        assert isinstance(font.scale, yex.value.Dimen)
        assert font.scale == yex.value.Dimen(12, "pt")

def test_font_from_tokens_with_scale_number(yex_test_fs):

    string = r"cmr10 scaled 12"

    with expander_on_string(string) as e:
        font = yex.font.Font.from_tokens(e)

        assert font.name == 'cmr10'
        assert isinstance(font.scale, yex.value.Number)
        assert font.scale == 12

def test_font_used(yex_test_fs):
    font = yex.font.Font.from_name('cmr10')
    assert list(font.used)==[]
    font[102] = yex.value.Dimen(12)

    assert font['A'].glyph is not None
    assert list(font.used)==[ord('A')]

    with pytest.raises(yex.exception.YexError):
        font[103] = yex.value.Dimen(12)

def test_font_glyphs(yex_test_fs):

    for fontname in [
            'cmr10', None,
            ]:
        font = yex.font.Font.from_name('cmr10')

        assert font['A'].glyph is not None, font

        found = '\n'.join(font['A'].glyph.ascii_art())
        expected = ENORMOUS_A
        assert found==expected, font

def test_font_glyph_image(yex_test_fs):
    font = yex.font.Font.from_name('cmr10')
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

def test_font_identifier(yex_test_fs):

    cmr10 = yex.font.Font.from_name('cmr10')
    assert cmr10.identifier == r'cmr10'

    nullfont = yex.font.Nullfont()
    assert nullfont.identifier == r'nullfont'

def test_font_from_name_resolve(fs,
        monkeypatch):

    def _pretend_expanduser(path):
        if path.startswith('~/'):
            return '/home/user/'+path[2:]
        else:
            return path

    monkeypatch.setattr(os.path, 'expanduser',
            _pretend_expanduser)

    fs.cwd = '/tmp'

    doc = yex.Document()

    PLACES = {
            'userfonts': '/home/user/.fonts/wombat.tfm',
            'cwd': '/tmp/wombat.tfm',
            'resources': None,
            # and probably others later
            }

    # plus something weird which will always be a negative
    WEIRD = '/home/user/untitled-goose-game'

    class FoundSomething(Exception):
        def __init__(self, what, *args, **kwargs):
            super().__init__(self, *args, **kwargs)
            self.what = what

        def __str__(self):
            return self.what

    class FakeTfm:
        def __init__(self, f, *args, **kwargs):
            logger.debug("our debugging fake font was found in: %s",
                    os.path.abspath(f.name))
            raise FoundSomething(os.path.abspath(f.name))

    class FakeImportlibResourcesFiles:
        def __init__(self, active=False):
            self.active = active
        @classmethod
        def create_factory(cls, is_active):
            def factory(_):
                return cls(active=is_active)

            return factory
        def __truediv__(self, _):
            return self
        def iterdir(self):
            class FakeFile:
                name = 'wombat.tfm'

                def open(self, _):
                    logger.debug("our debugging fake font was found "
                            "in the resources")
                    raise FoundSomething('resources')

            if self.active:
                logger.debug("fake resource: active; returning font")
                return [
                        FakeFile(),
                        ]
            else:
                logger.debug("fake resource: inactive; returning nothing")
                return []

    def run(which, expected):
        if not which:
            which = []
        else:
            which = which.split(' ')

        logger.debug("%s: going to look for a font; expecting %s",
                which, expected)

        remove = list(PLACES.values())
        remove.append(WEIRD)
        for filename in PLACES.values():
            if not filename:
                continue
            try:
                fs.remove_object(filename)
                logger.debug("%s: prep: rm %s", which, filename)
            except FileNotFoundError:
                pass

        available = [PLACES[n] for n in which if PLACES[n]]
        available.append(WEIRD)

        for filename in available:
            try:
                fs.create_file(
                    file_path = filename,
                    st_mode = 0o666,
                    contents = b'',
                    create_missing_dirs = True,
                    )
                logger.debug("%s: prep: create %s", which, filename)
            except FileExistsError:
                pass

        logger.debug("%s: here we go!", which)
        found = None
        try:
            with unittest.mock.patch('importlib.resources.files',
                    FakeImportlibResourcesFiles.create_factory(
                        is_active = 'resources' in which)):

                with unittest.mock.patch('yex.font.tfm.Tfm', FakeTfm):
                    font = yex.font.Font.from_name('wombat')
        except FoundSomething as e:
            found = e.what
            for f,v in PLACES.items():
                if found==v:
                    found = f
                    break
        except ValueError:
            found = 'nil'

        logger.debug("%s: found: %s; expected: %s",
                which, found, expected)
        assert found==expected, which

    run("cwd resources userfonts", expected="cwd")
    run("resources userfonts", expected="resources")
    run("userfonts", expected="userfonts")
    run("", expected="nil")

def test_default_font():

    default_font = yex.font.Font.from_name(None)
    cmr10 = yex.font.Font.from_name('cmr10')

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
