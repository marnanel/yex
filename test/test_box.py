import pytest
import io
from collections import namedtuple
import yex.box
import yex.document
from . import *

DummyCharMetric = namedtuple(
        'DummyCharMetric',
        ['width', 'height', 'depth', 'codepoint'],
        )

def test_box_simple():
    b = yex.box.Box(1, 2, 3)

def test_charbox():

    s = yex.document.Document()

    cb = yex.box.CharBox(
            font = s['_font'],
            ch = 'x',
            )

    assert int(cb.width) == 5
    assert int(cb.height) == 4
    assert int(cb.depth) == 0
    assert cb.ch == 'x'

def test_hbox():
    hb = yex.box.HBox()

    boxes = [
            yex.box.Box(width=10, height=20, depth=30),
            yex.box.Box(width=40, height=50, depth=60),
            yex.box.Box(width=70, height=80, depth=90),
            ]

    for box in boxes:
        hb.append(box)

    assert hb.width == 120
    assert hb.height == 80
    assert hb.depth == 90

def test_vbox():
    vb = yex.box.VBox()

    boxes = [
            yex.box.Box(width=10, height=20, depth=30),
            yex.box.Box(width=40, height=50, depth=60),
            yex.box.Box(width=70, height=80, depth=90),
            ]

    for box in boxes:
        vb.append(box)

    assert vb.width == 70
    assert vb.height == 330
    assert vb.depth == 0 # XXX check whether this is how it's supposed to work

def test_box_registers():
    """
    If you look up boxNN directly, it destroys the box.
    If you use the alias "copyNN", it doesn't.
    """

    s = yex.document.Document()
    s[r'\box23'] = yex.box.Box(width=20.0)
    assert s[r'\box23'].value.width == 20.0
    assert s[r'\box23'].value.width == 0.0

    s[r'\box23'] = yex.box.Box(width=20.0)
    assert s[r'\copy23'].value.width == 20.0
    assert s[r'\copy23'].value.width == 20.0
    assert s[r'\box23'].value.width == 20.0
    assert s[r'\box23'].value.width == 0.0
    assert s[r'\copy23'].value.width == 0.0

    s[r'\copy23'] = yex.box.Box(width=20.0)
    assert s[r'\copy23'].value.width == 20.0
    assert s[r'\box23'].value.width == 20.0
    assert s[r'\box23'].value.width == 0.0

def test_box_with_text_contents():
    s = yex.document.Document()

    message = 'Hello'

    run_code(
        r"\setbox23=\hbox{" + message + "}",
        doc=s,
        )
    font = s['_font']

    assert ''.join([x.ch for x in s[r'\copy23'].value.contents])==message

    expected_width = float(sum([
            font[c].metrics.width
            for c in message
            ]))

    assert round(
            float(s[r'\copy23'].value.width), 3
            )==round(expected_width, 3)

def test_setbox():
    s = yex.document.Document()
    run_code(
            r"\setbox23=\hbox{}",
            doc=s,
            )
    assert s[r'\box23'].value==yex.box.HBox()

def test_box_init_from_tokeniser():

    with io.StringIO("hello") as f:
        s = yex.document.Document()
        t = yex.parse.Tokeniser(s, f)

        with pytest.raises(yex.exception.YexError):
            box = yex.box.Box(t)

        with pytest.raises(yex.exception.YexError):
            hbox = yex.box.HBox(t)

def test_tex_logo_p66(capsys, ):
    string = (
        r"\setbox0=\hbox{T\kern-.1667em\lower.5ex\hbox{E}\kern-.125emX}"
        r"\showbox0"
        )
    expected = (
            # The TeXbook gives the font as "tenrm", but that's an alias
            # given in plain.tex, which isn't loaded here.
            r'\hbox(6.83331+2.15277)x18.6108' '\n'
            r'.\cmr10 T' '\n'
            r'.\kern -1.66702' '\n'
            r'.\hbox(6.83331+0.0)x6.80557, shifted 2.15277' '\n'
            r'..\cmr10 E' '\n'
            r'.\kern -1.25' '\n'
            r'.\cmr10 X' '\n'
            )

    assert run_code(
            string,
            find='chars',
            )==''

    found = capsys.readouterr().out

    print('-- Found')
    print(found)
    print('-- Expected')
    print(expected)

    compare_strings_with_reals(
            found,
            expected,
            tolerance=0.01,
            )

def test_wordbox_append_illegal_args():
    font = yex.font.get_font_from_name(None)
    wb = yex.box.WordBox(font=font)

    with pytest.raises(TypeError):
        wb.append(123)

    with pytest.raises(TypeError):
        wb.append(None)

    with pytest.raises(TypeError):
        wb.append('Hello world')

    with pytest.raises(TypeError):
        wb.append('')

def test_wordbox_width():
    font = yex.font.get_font_from_name(None)

    def total_lengths_of_chars(s):
        widths = max_height = max_depth = 0
        for c in s:
            metrics = font[c].metrics
            widths += metrics.width
            max_height = max(metrics.height, max_height)
            max_depth = max(metrics.depth, max_depth)
        return widths, max_height, max_depth

    # "expected" is the expected difference between the width of the word
    # and the total of the widths of all its characters.
    # The differences are caused by kerns and ligatures.
    for word, expected in [
            ('X',           0),
            ('XX',          0),
            ('I',           0),
            ('II',     -0.278), # there is a kern
            ('o',           0),
            ('of',          0),
            ('off',    -3.056), # "ff" ligature
            ('offi',   -5.834), # "ffi" ligature
            ('offic',  -5.834),
            ('office', -5.834),
            ]:
        wb = yex.box.WordBox(font=font)
        assert wb.width==0

        for c in word:
            wb.append(c)

        w, h, d = total_lengths_of_chars(word)

        # Height and depth aren't affected by kerns and ligatures
        assert wb.height == h, word
        assert wb.depth == d, word

        # But width is!
        difference = wb.width - w
        assert difference == yex.value.Dimen(expected), word
