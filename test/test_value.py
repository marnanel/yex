import io
import pytest
from mex.state import State
from mex.token import Token, Tokeniser
from mex.value import Number, Dimen

# TODO glue
# TODO muglue

def _get_number(number):
    """
    Creates a State and a Tokeniser, and tokenises the string
    you pass in. The string should represent a number followed
    by the letter "q" (so we can test how well numbers are
    delimited by the following characters).

    Returns the number.
    """

    state = State()

    with io.StringIO(number) as f:
        t = Tokeniser(state, f)

        result = Number(t)

        try:
            q = t.__next__()
        except StopIteration:
            raise ValueError("Wanted trailing 'q' for "
                    f"{number} but found nothing")

        if q.category==q.LETTER and q.ch=='q':
            return result.value
        else:
            raise ValueError(f"Wanted trailing 'q' for "
                    f"{number} but found {q}")

def _get_dimen(dimen,
        state = None):
    """
    Creates a State and a Tokeniser, and tokenises the string
    you pass in. The string should represent a dimen followed
    by the letter "q" (so we can test how well numbers are
    delimited by the following characters).

    If you supply a State, we use that State rather than
    creating a throwaway State.

    Returns the size in millimetres.
    """

    if state is None:
        state = State()

    with io.StringIO(dimen) as f:
        t = Tokeniser(state, f)

        result = Dimen(t)

        try:
            q = t.__next__()
        except StopIteration:
            raise ValueError("Wanted trailing 'q' for "
                    f"{dimen} but found nothing")

        if q.category==q.LETTER and q.ch=='q':
            return result.value
        else:
            raise ValueError(f"Wanted trailing 'q' for "
                    f"{dimen} but found {q}")

def test_number_decimal():
    assert _get_number('42q')==42

def test_number_octal():
    assert _get_number("'52q")==42

def test_number_hex():
    assert _get_number('"2aq')==42

def test_number_char():
    assert _get_number('`*q')==42

def test_number_control():
    assert _get_number('`\\{q')==123

def test_number_decimal_negative():
    assert _get_number('-42q')==-42

def test_number_octal_negative():
    assert _get_number("-'52q")==-42

def test_number_hex_negative():
    assert _get_number('-"2aq')==-42

def test_number_decimal_positive():
    assert _get_number('+42q')==42

def test_number_decimal_double_negative():
    assert _get_number('--42q')==42

def test_number_internal_integer():
    assert _get_number('\\count1q')==0

@pytest.mark.xfail
def test_number_internal_dimen():
    assert _get_number('\\hsize q')==0

@pytest.mark.xfail
def test_number_internal_glue():
    assert _get_number('\\skip100 q')==0

@pytest.mark.xfail
def test_integer_parameter():
    assert False

@pytest.mark.xfail
def test_special_integer():
    assert _get_number('\\spacefactor q')==0
    assert _get_number('\\prevgraf q')==0
    assert _get_number('\\deadcycles q')==0
    assert _get_number('\\insertpenalties q')==0

@pytest.mark.xfail
def test_lastpenalty():
    assert _get_number('\\lastpenalty q')==0

@pytest.mark.xfail
def test_countdef_token():
    assert False

@pytest.mark.xfail
def test_count_with_number():
    assert _get_number('\\count23 q')==234

@pytest.mark.xfail
def test_codename_with_number():
    assert _get_number('\\catcode23 q')==234
    assert _get_number('\\mathcode23 q')==234
    assert _get_number('\\lccode23 q')==234
    assert _get_number('\\uccode23 q')==234
    assert _get_number('\\sfcode23 q')==234
    assert _get_number('\\delcode23 q')==234

@pytest.mark.xfail
def test_chardef_token():
    assert False

@pytest.mark.xfail
def test_mathchardef_token():
    assert False

@pytest.mark.xfail
def test_parshape():
    assert _get_number('\\parshape q')==0

@pytest.mark.xfail
def test_inputlineno():
    assert _get_number('\\inputlineno q')==0

FONT = [
        '<fontdef token>', #XXX
        r'\font',
        r'\textfont7',
        r'\scriptfont7',
        r'\scriptscriptfont7',
        ]

@pytest.mark.xfail
def test_hyphenchar_skewchar():
    for font in FONT:
        assert _get_number(rf'\hyphenchar{font} q')==0
        assert _get_number(rf'\skewchar{font} q')==0

@pytest.mark.xfail
def test_badness():
    assert _get_number(r'\badness q')==0

################################

UNITS = [
        ("pt", 65536),
        ("pc", 786432),
        ("in", 4736286),
        ("bp", 65782),
        ("cm", 1864680),
        ("mm", 186468),
        ("dd", 70124),
        ("cc", 841489),
        ("sp", 1),
        ]

def test_dimen_physical_unit():
    for unit, size in UNITS:
        assert _get_dimen(f"3{unit}q")==size*3

def test_dimen_physical_unit_true():

    s = State()

    for unit, size in UNITS:
        assert _get_dimen(
                f"3{unit}q",
                state=s,
                )==size*3

    for unit, size in UNITS:
        assert _get_dimen(
                f"3true{unit}q",
                state=s,
                )==size*3

    s.begin_group()
    s.controls['mag'] = 2000
    for unit, size in UNITS:
        assert _get_dimen(
                f"3{unit}q",
                state=s,
                )==size*6

    for unit, size in UNITS:
        assert _get_dimen(
                f"3true{unit}q",
                state=s,
                )==size*3

    s.end_group()
    for unit, size in UNITS:
        assert _get_dimen(
                f"3{unit}q",
                state=s,
                )==size*3

    for unit, size in UNITS:
        assert _get_dimen(
                f"3true{unit}q",
                state=s,
                )==size*3

def test_dimen_texbook_p57_1():
    assert _get_dimen("3 inq")==14208858

def test_dimen_texbook_p57_2():
    assert _get_dimen("-.013837inq")==-65535

def test_dimen_texbook_p57_3():
    assert _get_dimen("0.mmq")==0

def test_dimen_texbook_p57_4():
    assert _get_dimen("29 pcq")==22806528

def test_dimen_texbook_p57_5():
    assert _get_dimen("+ 42,1 ddq")==2952220

def test_dimen_texbook_p57_6():
    assert _get_dimen("123456789spq")==123456789

def test_dimen_font_based_unit():

    s = State()

    assert _get_dimen(
            f"3emq",
            state=s,
            )==3

    assert _get_dimen(
            f"3exq",
            state=s,
            )==1

@pytest.mark.xfail
def test_dimen_parameter():
    assert False

@pytest.mark.xfail
def test_special_dimen():
    assert _get_dimen(r"\prevdepth q")==123456789
    assert _get_dimen(r"\pagegoal q")==123456789
    assert _get_dimen(r"\pagetotal q")==123456789
    assert _get_dimen(r"\pagestretch q")==123456789
    assert _get_dimen(r"\pagefilstretch q")==123456789
    assert _get_dimen(r"\pagefillstretch q")==123456789
    assert _get_dimen(r"\pagefilllstretch q")==123456789
    assert _get_dimen(r"\pageshrink q")==123456789
    assert _get_dimen(r"\pagedepth q")==123456789

@pytest.mark.xfail
def test_lastkern():
    assert _get_dimen(r"\lastkern q")==123456789

@pytest.mark.xfail
def test_dimendef_token():
    assert False

@pytest.mark.xfail
def test_dimen_with_number():
    assert _get_dimen(r"\dimen23 q")==123456789

@pytest.mark.xfail
def test_boxdimen_with_number():
    for dimension in [
            'ht', 'wd', 'dp',
            ]:
        assert _get_dimen(rf"\{dimension}23 q")==123456789

@pytest.mark.xfail
def test_fontdimen():
    for font in FONT:
        assert _get_dimen(rf'\fontdimen23{font} q')==0
