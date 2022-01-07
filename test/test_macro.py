import io
from mex.state import State
from mex.macro import add_macros_to_state

def test_add_macros_to_state():
    s = State()
    assert s['macro catcode'] is None

    add_macros_to_state(s)
    assert s['macro catcode'] is not None
