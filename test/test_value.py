import io
import pytest
from mex.state import State
from mex.parse import Token, Tokeniser
from mex.value import Number, Dimen
import mex.put

# TODO glue
# TODO muglue

def _get_number(number,
        state = None):
    """
    Creates a State and a Tokeniser, and tokenises the string
    you pass in. The string should represent a number followed
    by the letter "q" (so we can test how well numbers are
    delimited by the following characters).

    Returns the number.
    """

    if state is None:
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

@pytest.mark.xfail
def test_number_internal_integer():
    assert _get_number('\\count1q')==0

@pytest.mark.xfail
def test_number_internal_dimen():
    assert _get_number('\\hsize q')==0

@pytest.mark.xfail
def test_number_internal_glue():
    assert _get_number('\\skip100 q')==0

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

def test_count_with_number():
    s = State()
    s['count23'] = 234
    assert _get_number('\\count23q', s)==234

def test_codename_with_number():
    assert _get_number('\\catcode65q')==11 # "A" == letter
    assert _get_number('\\mathcode65q')==0x7100+65
    assert _get_number('\\sfcode23q')==1000
    assert _get_number('\\sfcode65q')==999
    assert _get_number('\\delcode23q')==-1
    assert _get_number('\\delcode46q')==0

def test_upper_and_lower_case():
    assert _get_number('\\lccode65q')==ord('a')
    assert _get_number('\\uccode65q')==ord('A')

    assert _get_number('\\lccode97q')==ord('a')
    assert _get_number('\\uccode97q')==ord('A')

@pytest.mark.xfail
def test_chardef_token():
    assert False

@pytest.mark.xfail
def test_mathchardef_token():
    assert False

@pytest.mark.xfail
def test_parshape():
    assert _get_number('\\parshape q')==0

def test_inputlineno():
    s = State()
    assert _get_number(r'\inputlineno q',s)==1
    assert _get_number(r'\inputlineno q',s)==1
    mex.put.put('\n', s)
    assert _get_number(r'\inputlineno q',s)==2
    mex.put.put('\n', s)
    assert _get_number(r'\inputlineno q',s)==3
    assert _get_number(r'\inputlineno q',s)==3

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
    s['mag'] = 2000
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

def test_arithmetic_add_count():
    state = State()

    numbers = []

    for n in ['100', '77']:
        with io.StringIO(n) as f:
            t = Tokeniser(state, f)
            numbers.append(Number(t))

    assert numbers[0].value==100
    assert numbers[1].value==77

    numbers[0] += numbers[1]
    assert numbers[0].value==177

    with io.StringIO("2sp") as f:
        t = Tokeniser(state, f)
        d = Dimen(t)

    with pytest.raises(TypeError): numbers[0] += d

def test_arithmetic_add_dimen():
    state = State()

    dimens = []

    for n in ['1sp', '7sp']:
        with io.StringIO(n) as f:
            t = Tokeniser(state, f)
            dimens.append(Number(t))

    assert dimens[0].value==1
    assert dimens[1].value==7

    dimens[0] += dimens[1]
    assert dimens[0].value==8

def test_arithmetic_multiply_divide():
    state = State()

    numbers = []

    for n in ['100', '100', '2']:
        with io.StringIO(n) as f:
            t = Tokeniser(state, f)
            numbers.append(Number(t))

    with io.StringIO("2sp") as f:
        t = Tokeniser(state, f)
        d = Dimen(t)

    assert [x.value for x in numbers]==[100, 100, 2]

    numbers[0] *= numbers[2]
    numbers[1] /= numbers[2]

    assert [x.value for x in numbers]==[200, 50, 2]

    # Things that shouldn't work

    with pytest.raises(TypeError): numbers[0] *= d
    with pytest.raises(TypeError): numbers[0] /= d
    with pytest.raises(TypeError): d *= d
    with pytest.raises(TypeError): d /= d
    with pytest.raises(TypeError): d *= numbers[0]
    with pytest.raises(TypeError): d /= numbers[0]

def test_dimen_with_name_of_other_dimen():

    state = State()
    string = r'\dimen1=100mm \dimen2=\dimen1'

    mex.put.put(string, state=state)

    assert str(state['dimen1'].value)== \
            str(state['dimen2'].value)

def test_number_from_count():
    """
    This is a regression test for a bug where calling int()
    on a count register initialised from another count register
    caused TypeError; see the commit message for why.
    """

    state = State()
    state['count1'] = 100

    with io.StringIO(r'\count1') as f:
        t = Tokeniser(state, f)
        n = Number(t)

    assert n==100
    assert int(n)==100

def test_dimen_with_no_unit():
    with pytest.raises(mex.exception.ParseError):
        _get_dimen("123")
