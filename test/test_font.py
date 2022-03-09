from . import *
import mex.font
import mex.state
import mex.parse
import io

def test_font_none():
    font = mex.font.Font()
    assert font.filename == None
    assert font.name == None
    assert font.scale == None

def test_font_literal():
    font = mex.font.Font(
            filename = '/tmp/wombat.tfm')
    assert font.filename == '/tmp/wombat.tfm'
    assert font.name == 'wombat'
    assert font.scale == None

def test_font_literal_with_scale_dimen():
    font = mex.font.Font(
            filename = '/tmp/wombat.tfm',
            scale = mex.value.Dimen(12, "pt"))
    assert font.filename == '/tmp/wombat.tfm'
    assert font.name == 'wombat'
    assert isinstance(font.scale, mex.value.Dimen)
    assert font.scale == mex.value.Dimen(12, "pt")

def test_font_literal_with_scale_number():
    font = mex.font.Font(
            filename = '/tmp/wombat.tfm',
            scale = mex.value.Number(12))
    assert font.filename == '/tmp/wombat.tfm'
    assert font.name == 'wombat'
    assert isinstance(font.scale, mex.value.Number)
    assert font.scale == 12

def test_font_from_tokens():
    state = mex.state.State()

    string = r"/tmp/wombat.tfm"

    with expander_on_string(string) as e:
        font = mex.font.Font(
                tokens = e)
        assert font.filename == '/tmp/wombat.tfm'
        assert font.name == 'wombat'
        assert font.scale == None

def test_font_from_tokens_with_scale_dimen():

    string = r"/tmp/wombat.tfm at 12pt"

    with expander_on_string(string) as e:
        font = mex.font.Font(
                tokens = e)
        assert font.filename == '/tmp/wombat.tfm'
        assert font.name == 'wombat'
        assert isinstance(font.scale, mex.value.Dimen)
        assert font.scale == mex.value.Dimen(12, "pt")

def test_font_from_tokens_with_scale_number():

    string = r"/tmp/wombat.tfm scaled 12"

    with expander_on_string(string) as e:
        font = mex.font.Font(
                tokens = e)
        assert font.filename == '/tmp/wombat.tfm'
        assert font.name == 'wombat'
        assert isinstance(font.scale, mex.value.Number)
        assert font.scale == 12
