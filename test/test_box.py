import pytest
import io
from collections import namedtuple
import mex.box
import mex.state
from . import *

DummyCharMetric = namedtuple(
        'DummyCharMetric',
        ['width', 'height', 'depth', 'codepoint'],
        )

def test_box_simple():
    b = mex.box.Box(1, 2, 3)

def test_charbox():

    s = mex.state.State()

    cb = mex.box.CharBox(
            font = s['_font'],
            ch = 'x',
            )

    assert float(cb.width) == 345886.25
    assert float(cb.height) == 282168.75
    assert float(cb.depth) == 0.0
    assert cb.ch == 'x'

def test_hbox():
    hb = mex.box.HBox()

    boxes = [
            mex.box.Box(width=10, height=20, depth=30),
            mex.box.Box(width=40, height=50, depth=60),
            mex.box.Box(width=70, height=80, depth=90),
            ]

    for box in boxes:
        hb.append(box)

    assert hb.width == 120
    assert hb.height == 80
    assert hb.depth == 90

def test_vbox():
    vb = mex.box.VBox()

    boxes = [
            mex.box.Box(width=10, height=20, depth=30),
            mex.box.Box(width=40, height=50, depth=60),
            mex.box.Box(width=70, height=80, depth=90),
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

    s = mex.state.State()
    s['box23'] = mex.box.Box(width=20.0)
    assert s['box23'].value.width == 20.0
    assert s['box23'].value.width == 0.0

    s['box23'] = mex.box.Box(width=20.0)
    assert s['copy23'].value.width == 20.0
    assert s['copy23'].value.width == 20.0
    assert s['box23'].value.width == 20.0
    assert s['box23'].value.width == 0.0
    assert s['copy23'].value.width == 0.0

    s['copy23'] = mex.box.Box(width=20.0)
    assert s['copy23'].value.width == 20.0
    assert s['box23'].value.width == 20.0
    assert s['box23'].value.width == 0.0

def test_box_with_text_contents():
    s = mex.state.State()

    message = 'Hello'

    run_code(
        r"\setbox23=\hbox{" + message + "}",
        state=s,
        )
    metrics = s['_font'].metrics

    assert ''.join([x.ch for x in s['copy23'].value.contents])==message

    expected_width = float(sum([
            metrics[c].width
            for c in message
            ]))

    assert round(
            s['copy23'].value.width.value, 3
            )==round(expected_width*65536, 3)

def test_setbox():
    s = mex.state.State()
    run_code(
            r"\setbox23=\hbox{}",
            state=s,
            )
    assert s['box23'].value==mex.box.HBox()

def test_box_init_from_tokeniser():

    with io.StringIO("hello") as f:
        s = mex.state.State()
        t = mex.parse.Tokeniser(s, f)

        with pytest.raises(mex.exception.MexError):
            box = mex.box.Box(t)

        with pytest.raises(mex.exception.MexError):
            hbox = mex.box.HBox(t)

def test_tex_logo_p66(capsys):
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
            find='ch',
            )==''

    found = capsys.readouterr().out

    compare_strings_with_reals(
            found,
            expected,
            tolerance=0.01,
            )
