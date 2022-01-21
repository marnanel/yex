import io
from mex.state import State
from mex.macro import add_macros_to_state, Expander
from mex.token import Tokeniser

def test_add_macros_to_state():
    s = State()
    assert s['macro catcode'] is None

    add_macros_to_state(s)
    assert s['macro catcode'] is not None

def test_expand_simple():
    s = State()
    t = Tokeniser(s)
    e = Expander(t)

    string = "This is a test"

    with io.StringIO(string) as f:
        result = ''.join([
            t.ch for t in e.read(f)
            ])

    assert(result==string)

def test_expand_simple_def():
    s = State()
    t = Tokeniser(s)
    e = Expander(t)

    string = "\\def\\wombat{Wombat}\\wombat"

    with io.StringIO(string) as f:
        result = ''.join([
            t.ch for t in e.read(f)
            ])

    assert(result=="Wombat")
