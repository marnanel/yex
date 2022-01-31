import io
import pytest
from mex.state import State
from mex.macro import Expander
from mex.token import Tokeniser
import mex.put

def _test_expand(string, s=None, *args, **kwargs):

    if s is None:
        s = State()

    with io.StringIO(string) as f:
        t = Tokeniser(
                state = s,
                source = f,
                )

        e = Expander(t,
                *args, **kwargs)

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

def test_expand_with_single():
    assert _test_expand(r"This is a test",
            single=False)=="This is a test"

    assert _test_expand(r"This is a test",
            single=True)=="T"

    assert _test_expand(r"{This is} a test",
            single=False)=="{This is} a test"

    assert _test_expand(r"{This is} a test",
            single=True)=="This is"

    assert _test_expand(r"{Thi{s} is} a test",
            single=False)=="{Thi{s} is} a test"

    assert _test_expand(r"{Thi{s} is} a test",
            single=True)=="Thi{s} is"

def test_expand_with_running_and_single():
    assert _test_expand(r"{\def\wombat{x}\wombat} a test",
            single=True)=="x"
    assert _test_expand(r"{\def\wombat{x}\wombat} a test",
            single=True, running=False)==r"\def\wombat{x}\wombat"

def test_expand_with_running():
    assert _test_expand(r"\def\wombat{x}\wombat",
            running=True)=="x"

    assert _test_expand(r"\def\wombat{x}\wombat",
            running=False)==r"\def\wombat{x}\wombat"

    s = State()

    with io.StringIO(r"\def\wombat{x}\wombat\wombat\wombat") as f:
        t = Tokeniser(
                state = s,
                source = f,
                )

        e = Expander(t, running=True)

        t1 = e.__next__()
        assert str(t1)=='x'

        e.running=False
        t2 = e.__next__()
        assert str(t2)==r'\wombat'

        e.running=True
        t3 = e.__next__()
        assert str(t3)=='x'

def test_expand_with_running():
    s = State()

    with io.StringIO(r"abc") as f:
        t = Tokeniser(
                state = s,
                source = f,
                )

        e1 = Expander(t)

        t1 = e1.__next__()
        assert t1.ch=='a'

        e2 = Expander(t)
        t2 = e2.__next__()
        assert t2.ch=='b'

        t3 = e1.__next__()
        assert t3.ch=='c'

def test_expand_ex_20_2():
    string = r"\def\a{\b}" +\
            r"\def\b{A\def\a{B\def\a{C\def\a{\b}}}}" +\
            r"\def\puzzle{\a\a\a\a\a}" +\
            r"\puzzle"
    assert _test_expand(string)=="ABCAB"

def test_expand_params_p200():
    # I've replaced \\ldots with ... because it's not
    # pre-defined here.
    string = r"\def\row#1{(#1_1,...,#1_n)}\row x"
    assert _test_expand(string)==r"(x_1,...,x_n)"

def test_expand_params_p201():
    # I've replaced \\ldots with ... because it's not
    # pre-defined here.
    string = r"\def\row#1#2{(#1_1,...,#1_#2)}\row xn"
    assert _test_expand(string)==r"(x_1,...,x_n)"

def test_expand_params_basic_shortargument():
    string = "\\def\\hello#1{a#1b}\\hello 1"
    assert _test_expand(string)=="a1b"

def test_expand_params_basic_longargument():
    string = "\\def\\hello#1{a#1b}\\hello {world}"
    assert _test_expand(string)=="aworldb"

def test_expand_long_def():
    s = State()

    _test_expand("\\long\\def\\ab#1{a#1b}", s)
    _test_expand("\\def\\cd#1{c#1d}", s)

    assert s['ab'].is_long == True
    assert _test_expand("\\ab z", s)=="azb"
    assert _test_expand("\\ab \\par", s)=="ab"

    assert s['cd'].is_long == False
    assert _test_expand("\\cd z", s)=="czd"
    with pytest.raises(mex.exception.ParseError):
        _test_expand("\\cd \\par", s)

def test_expand_outer():

    # Per the TeXbook, p.205, \outer macros may not appear
    # in several places. We don't test all of them yet
    # (marked with a *), but we will. (TODO.) They are:
    #
    #  - In a macro argument
    #  - Param text of definition *
    #  - Replacement text of definition
    #  - Preamble to alignment *
    #  - Conditional text which is being skipped over *

    s = State()
    _test_expand("\\outer\\def\\wombat{W}", s)
    _test_expand("\\def\\notwombat{W}", s)
    _test_expand("\\def\\spong#1{Spong}", s)

    assert s['wombat'].is_outer == True
    assert s['notwombat'].is_outer == False

    for forbidden in [
            r'\spong{%s}', # Macro argument
            r'\def\fred#1%s#2{fred}', # Param text
            r'\def\fred#1{fred#1}\fred %s', # Replacement text
            ]:

        with pytest.raises(mex.exception.ParseError):
            _test_expand(forbidden % (r'\wombat',), s)

        _test_expand(forbidden % (r'\notwombat',), s)

def test_expand_edef_flag():
    s = State()
    string = "\\edef\\wombat{Wombat}\\wombat"
    assert _test_expand(string, s)=="Wombat"
    assert s['wombat'].is_expanded == True

def test_expand_long_long_long_def_flag():
    s = State()
    string = "\\long\\long\\long\\def\\wombat{Wombat}\\wombat"
    assert _test_expand(string, s)=="Wombat"
    assert s['wombat'].is_long == True

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

    state.end_group()

    result = _test_expand(
            "\\wombat",
            state)
    assert result=="Wombat"

    state.begin_group()

    result = _test_expand(
            "\\wombat" +\
            form_of_def + "\\wombat{Spong}" +\
            "\\wombat",
            state)
    assert result=="WombatSpong"

    state.end_group()

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
    _expand_global_def("\\xdef", s)
    assert s['wombat'].is_expanded == True

def test_catcode():
    # We set the catcode of ";" to 14, which makes it
    # a comment symbol.
    string = r";what\catcode`;=14 ;what"
    assert mex.put.put(string)==";what"

def test_chardef():
    string = r"\chardef\banana=98wom\banana at"
    assert mex.put.put(string)=="wombat"
