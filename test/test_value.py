import io
import pytest
from mex.state import State
from mex.parse import Token, Tokeniser
from mex.value import Number, Dimen, Glue
from . import *
import mex.put
import mex.box
import logging

general_logger = logging.getLogger('mex.general')

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
            general_logger.debug("tokenising %s", n)
            t = Tokeniser(state, f)
            numbers.append(Number(t))

    assert numbers[0].value==100
    assert numbers[1].value==77

    numbers[0] += numbers[1]
    assert numbers[0].value==177

    with io.StringIO("2sp") as f:
        t = Tokeniser(state, f)
        d = Dimen(t)
        with pytest.raises(TypeError):
            numbers[0] += d

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

# Glue

def test_glue_variable():

    VARIABLES = [
            "baselineskip",
            "lineskip",
            "parskip",
            "abovedisplayskip",
            "abovedisplayshortskip",
            "belowdisplayskip",
            "belowdisplayshortskip",
            "leftskip",
            "rightskip",
            "topskip",
            "splittopskip",
            "tabskip",
            "spaceskip",
            "xspaceskip",
            "parfillskip",

            "skip77",
            #"wombat",
            ]

    s = State()

    mex.put.put(r"\skipdef\wombat=100", s)

    for i, variable in enumerate(VARIABLES):
        s[variable] = mex.value.Glue(space=i)

    for i, variable in enumerate(VARIABLES):
        assert _get_glue(rf"\{variable} q",s) == (i, 0.0, 0.0, 0.0, 0)

def test_glue_literal():
    assert _get_glue("2spq") == (2.0, 0.0, 0.0, 0, 0)
    assert _get_glue("2sp plus 5spq") == (2.0, 5.0, 0.0, 0, 0)
    assert _get_glue("2sp minus 5spq") == (2.0, 0.0, 5.0, 0, 0)
    assert _get_glue("2sp plus 5sp minus 5spq") == (2.0, 5.0, 5.0, 0, 0)

def test_glue_literal_fil():
    assert _get_glue("2sp plus 5fil minus 5fillq") == (2.0, 5.0, 5.0, 1, 2)
    assert _get_glue("2sp plus 5filll minus 5fillq") == (2.0, 5.0, 5.0, 3, 2)

def test_glue_repr():
    def _test_repr(s):
        assert str(_get_glue(f'{s}q', raw=True)) == s

    _test_repr('2.0pt plus 5.0pt')
    _test_repr('2.0pt plus 5fil')
    _test_repr('2.0pt plus 5fill')
    _test_repr('2.0pt plus 5filll minus 5fil')

def test_glue_p69():
    hb = mex.box.HBox()

    boxes = [
            # This is the example on p69 of the TeXbook.

            mex.box.Box(width=5, height=10, depth=0),
            mex.value.Glue(space=9.0, stretch=3, shrink=1),
            mex.box.Box(width=6, height=20, depth=0),
            mex.value.Glue(space=9.0, stretch=6, shrink=2),
            mex.box.Box(width=3, height=30, depth=0),
            mex.value.Glue(space=12.0, stretch=0, shrink=0),
            mex.box.Box(width=8, height=40, depth=0),
            ]

    def glue_lengths():
        return [g.length.value for g in boxes
                if isinstance(g, mex.value.Glue)]

    hb = mex.box.HBox(boxes)

    assert hb.width == 52
    assert hb.height == 40
    assert glue_lengths() == [9.0, 9.0, 12.0]

    hb.fit_to(58)

    assert hb.width == 58
    assert hb.height == 40
    assert glue_lengths() == [11.0, 13.0, 12.0]

    hb.fit_to(51)

    assert hb.width == 51
    assert hb.height == 40
    assert [round(x,2) for x in glue_lengths()] == [
            8.67, 8.33, 12.0,
            ]

    hb.fit_to(0)

    assert hb.width == 49
    assert hb.height == 40
    assert glue_lengths() == [8.0, 7.0, 12.0]

    boxes[1] = mex.value.Glue(space=9.0, stretch=3, shrink=1, stretch_infinity=1)
    hb = mex.box.HBox(boxes)

    hb.fit_to(58)

    assert hb.width == 58
    assert hb.height == 40
    assert glue_lengths() == [15.0, 9.0, 12.0]

    boxes[3] = mex.value.Glue(space=9.0, stretch=6, shrink=2, stretch_infinity=1)
    hb = mex.box.HBox(boxes)

    hb.fit_to(58)

    assert hb.width == 58
    assert hb.height == 40
    assert glue_lengths() == [11.0, 13.0, 12.0]

    boxes[3] = mex.value.Glue(space=9.0, stretch=6, shrink=2, stretch_infinity=2)
    hb = mex.box.HBox(boxes)

    hb.fit_to(58)

    assert hb.width == 58
    assert hb.height == 40
    assert glue_lengths() == [9.0, 15.0, 12.0]

def test_muglue_literal():
    assert _get_muglue("2muq") == (2.0, 0.0, 0.0, 0, 0)
    assert _get_muglue("2mu plus 5muq") == (2.0, 5.0, 0.0, 0, 0)
    assert _get_muglue("2mu minus 5muq") == (2.0, 0.0, 5.0, 0, 0)
    assert _get_muglue("2mu plus 5mu minus 5muq") == (2.0, 5.0, 5.0, 0, 0)

def test_muglue_literal_fil():
    assert _get_muglue("2mu plus 5fil minus 5fillq") == (2.0, 5.0, 5.0, 1, 2)
    assert _get_muglue("2mu plus 5filll minus 5fillq") == (2.0, 5.0, 5.0, 3, 2)

def test_muglue_repr():
    def _test_repr(s):
        assert str(_get_muglue(f'{s}q', raw=True)) == s

    _test_repr('2.0mu plus 5.0mu')
    _test_repr('2.0mu plus 5fil')
    _test_repr('2.0mu plus 5fill')
    _test_repr('2.0mu plus 5filll minus 5fil')
