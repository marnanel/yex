import io
import pytest
from mex.state import State
from mex.macro import Expander
from mex.parse import Tokeniser
import mex.font
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
    assert _test_expand(string)=="Wombat"

def test_expand_with_single():
    assert _test_expand(r"This is a test",
            single=False)=="This is a test"

    assert _test_expand(r"This is a test",
            single=True)=="T"

    assert _test_expand(r"{This is} a test",
            single=False)=="This is a test"

    assert _test_expand(r"{This is} a test",
            single=True)=="This is"

    assert _test_expand(r"{Thi{s} is} a test",
            single=False)=="This is a test"

    assert _test_expand(r"{Thi{s} is} a test",
            single=True)=="This is"

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

        with pytest.raises(mex.exception.MacroError):
            _test_expand(forbidden % (r'\wombat',), s)

        _test_expand(forbidden % (r'\notwombat',), s)

def test_expand_edef():

    # From p214 of the TeXbook
    basic_test = r'\def\double#1{#1#1}'+\
            r'\edef\a{\double{xy}}\a'+\
            r'\edef\a{\double\a}\a'
    basic_result = "xy"*6

    assert _test_expand(basic_test)==basic_result

    assert _test_expand(r'{'+basic_test+r'}')==\
            basic_result

    assert _test_expand(r'{'+basic_test+r'}\a')==\
            basic_result+'a'

    assert _test_expand(r'{'+\
            basic_test.replace(r'\edef', r'\xdef')+\
            r'}\a')==\
            basic_result+'xy'*4

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

def test_catcode():
    # We set the catcode of ";" to 14, which makes it
    # a comment symbol.
    string = r";what\catcode`;=14 ;what"
    assert _test_expand(string)==";what"

def test_chardef():
    string = r"\chardef\banana=98wom\banana at"
    assert _test_expand(string)=="wombat"

def test_mathchardef():
    string = r'\mathchardef\sum="1350'
    mex.put.put(string)
    # XXX This does nothing useful yet,
    # XXX but we have the test here to make sure it parses

def _test_expand_the(string, s=None, *args, **kwargs):

    if s is None:
        s = State()

    result = ''

    with io.StringIO(string) as f:
        t = Tokeniser(
                state = s,
                source = f,
                )

        e = Expander(t,
                *args, **kwargs)

        for c in e:
            if c.ch==32: 
                assert c.category==10 
            else: 
                assert c.category==12 

            result += c.ch

    return result

def test_the_count():
    string = r'\count20=177\the\count20'
    assert _test_expand_the(string) == '177'

def test_the_dimen():
    string = r'\dimen20=20pt\the\dimen20'
    assert _test_expand_the(string) == '20.0pt'

def test_let_p206_1():
    string = r'\let\a=\def \a\b{hello}\b'
    assert _test_expand(string) == 'hello'

def test_let_p206_2():
    string = r'\def\b{x}\def\c{y}'+\
            r'\b\c'+\
            r'\let\a=\b \let\b=\c \let\c=\a'+\
            r'\b\c'
    assert _test_expand(string) == 'xyyx'

def _test_font_control(
        string,
        s = None,
        ):

    if s is None:
        s = State()

    return s['_currentfont'].value

def test_font_control_simple(fs, monkeypatch):

    fs.create_file(r'wombat.tfm')

    def pretend_metrics_constructor(self, filename):
        self.this_is_wombat = True

    monkeypatch.setattr(mex.font.Metrics, '__init__',
            pretend_metrics_constructor)

    metrics = _test_font_control(
        string = r'\font\wombat=wombat \wombat'
        )

    assert metrics.this_is_wombat

def test_countdef():
    string = r'\count28=17 '+\
            r'\countdef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18'+\
            r'\the\count28'
    assert _test_expand(string) == '1718'

def test_dimendef():
    string = r'\dimen28=17pt'+\
            r'\dimendef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18pt'+\
            r'\the\dimen28'
    assert _test_expand(string) == '17.0pt18.0pt'

@pytest.mark.xfail
def test_skipdef():
    string = r'\skip28=17 plus 0pt minus 0pt'+\
            r'\skipdef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18 plus 0pt minus 0pt'+\
            r'\the\skip28'
    assert _test_expand(string) == '17 plus 0pt minus 0pt18 plus 0pt minus 0pt'

@pytest.mark.xfail
def test_muskipdef():
    string = r'\muskip28=17 plus 0pt minus 0pt'+\
            r'\muskipdef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18 plus 0pt minus 0pt'+\
            r'\the\muskip28'
    assert _test_expand(string) == '17 plus 0pt minus 0pt18 plus 0pt minus 0pt'

# Arithmetic

def test_advance_count():
    assert _test_expand(
            r'\count10=100'+\
                    r'\advance\count10 by 5 '+\
                    r'\the\count10') == '105'

def test_advance_dimen():
    assert _test_expand(
            r'\dimen10=10pt'+\
                    r'\advance\dimen10 by 5pt'+\
                    r'\the\dimen10') == '15.0pt'

def test_multiply():
    assert _test_expand(
            r'\count10=100'+\
                    r'\multiply\count10 by 5 '+\
                    r'\the\count10') == '500'

def test_divide():
    assert _test_expand(
            r'\count10=100'+\
                    r'\divide\count10 by 5 '+\
                    r'\the\count10') == '20.0'
