import io
from mex.state import State
from mex.macro import add_macros_to_state, Expander
from mex.token import Tokeniser

def test_add_macros_to_state():
    s = State()
    assert s['macro catcode'] is None

    add_macros_to_state(s)
    assert s['macro catcode'] is not None

def _test_expand(string):

    s = State()

    with io.StringIO(string) as f:
        t = Tokeniser(
                state = s,
                source = f,
                )
        e = Expander(t)

        result = ''.join([t.ch for t in e])

    return result

def test_expand_simple():
    string = "This is a test"
    assert _test_expand(string) == string

def test_expand_simple_def():
    string = "\\def\\wombat{Wombat}\\wombat"
    assert _test_expand(string)=="Wombat"

def test_expand_simple_with_nested_braces():
    string = "\\def\\wombat{Wom{b}at}\\wombat"
    assert _test_expand(string)=="Wom{b}at"


