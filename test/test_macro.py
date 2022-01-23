import io
from mex.state import State
from mex.macro import add_macros_to_state, Expander
from mex.token import Tokeniser

def test_add_macros_to_state():
    s = State()
    assert s['macro catcode'] is None

    add_macros_to_state(s)
    assert s['macro catcode'] is not None

def _test_expand(string, s=None):

    if s is None:
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

def test_expand_long_def_flag():
    s = State()
    string = "\\long\\def\\wombat{Wombat}\\wombat"
    assert _test_expand(string, s)=="Wombat"
    assert s['macro wombat'].is_long == True

def test_expand_outer_def_flag():
    s = State()
    string = "\\outer\\def\\wombat{Wombat}\\wombat"
    assert _test_expand(string, s)=="Wombat"
    assert s['macro wombat'].is_outer == True

def test_expand_edef_flag():
    s = State()
    string = "\\edef\\wombat{Wombat}\\wombat"
    assert _test_expand(string, s)=="Wombat"
    assert s['macro wombat'].is_expanded == True

def test_expand_long_long_long_def_flag():
    s = State()
    string = "\\long\\long\\long\\def\\wombat{Wombat}\\wombat"
    assert _test_expand(string, s)=="Wombat"
    assert s['macro wombat'].is_long == True

# XXX TODO Integration testing of edef is best done when
# XXX macro parameters are working.

def _expand_global_def(form_of_def, state=None):

    if state is None:
        state = State()

    result = _test_expand(
            "\\def\\wombat{Wombat}" +\
            "\\wombat",
            state,
            )
    assert result=="Wombat"

    state.begin_group()

    result = _test_expand(
            "\\wombat" +\
            "\\def\\wombat{Spong}" +\
            "\\wombat",
            state)
    assert result=="WombatSpong"

    result = _test_expand(
            "\\wombat",
            state)
    assert result=="Wombat"

    result = _test_expand(
            "\\wombat" +\
            form_of_def + "\\wombat{Spong}" +\
            "\\wombat",
            state)
    assert result=="WombatSpong"

    result = _test_expand(
            "\\wombat",
            state)
    assert result=="Spong"

def test_expand_global_def():
    _expand_global_def("\\global\\def")

def test_expand_gdef():
    _expand_global_def("\\gdef")

def test_expand_xdef():
    s = State()
    _expand_global_def("\\gdef", s)
    assert s['macro wombat'].is_expanded == True
