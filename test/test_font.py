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

def test_font_literal_with_scale():
    font = mex.font.Font(
            filename = '/tmp/wombat.tfm',
            scale = mex.value.Dimen(12, "pt"))
    assert font.filename == '/tmp/wombat.tfm'
    assert font.name == 'wombat'
    assert font.scale == mex.value.Dimen(12, "pt")

def _tokeniser(string, state=None):
    if state is None:
        state = mex.state.State()

    with io.StringIO(string) as f:
        result = mex.parse.Tokeniser(state, f)
        return result

def test_font_from_tokens():
    state = mex.state.State()

    string = r"/tmp/wombat.tfm"

    with io.StringIO(string) as f:
        t = mex.parse.Tokeniser(state, f)

        font = mex.font.Font(
                tokens = t)
        assert font.filename == '/tmp/wombat.tfm'
        assert font.name == 'wombat'
        assert font.scale == None

def test_font_from_tokens_with_scale():
    state = mex.state.State()

    string = r"/tmp/wombat.tfm at 12pt"

    with io.StringIO(string) as f:
        t = mex.parse.Tokeniser(state, f)

        font = mex.font.Font(
                tokens = t)
        assert font.filename == '/tmp/wombat.tfm'
        assert font.name == 'wombat'
        assert font.scale == mex.value.Dimen(12, "pt")
