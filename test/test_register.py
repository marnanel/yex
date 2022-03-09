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

    assert expand(
            r"\the\toks23",
            s)=='Hello'
