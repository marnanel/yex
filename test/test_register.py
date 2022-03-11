from mex.value import Tokenlist
import mex.parse
import mex.state
from . import *

def test_register_tokenlist():
    s = mex.state.State()

    assert s['toks23']==''

    assert expand(
            r"\toks23={Hello}",
            s)==''

    assert s['toks23']=='Hello'

    assert call_macro(
            call = r"\the\toks23",
            state = s)=='Hello'
