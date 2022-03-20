from yex.value import Tokenlist
import yex.parse
import yex.state
from . import *

def test_register_tokenlist():
    state = yex.state.State()

    assert state['toks23']==''

    assert run_code(
            r"\toks23={Hello}",
            state=state,
            find = 'chars',
            )==''

    assert state['toks23']=='Hello'

    assert run_code(
            call = r"\the\toks23",
            state = state,
            find = 'chars',
            )=='Hello'
