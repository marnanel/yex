import io
import pytest
from mex.state import State
from mex.parse import Token, Tokeniser, Expander
from mex.value import Number, Dimen, Glue
import mex.exception
from .. import *
import mex.box
import logging

general_logger = logging.getLogger('mex.general')

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
        assert get_dimen(f"3{unit}q")==size*3

def test_dimen_physical_unit_true():

    s = State()

    for unit, size in UNITS:
        assert get_dimen(
                f"3{unit}q",
                state=s,
                )==size*3

    for unit, size in UNITS:
        assert get_dimen(
                f"3true{unit}q",
                state=s,
                )==size*3

    s.begin_group()
    s['mag'] = 2000
    for unit, size in UNITS:
        assert get_dimen(
                f"3{unit}q",
                state=s,
                )==size*6

    for unit, size in UNITS:
        assert get_dimen(
                f"3true{unit}q",
                state=s,
                )==size*3

    s.end_group()
    for unit, size in UNITS:
        assert get_dimen(
                f"3{unit}q",
                state=s,
                )==size*3

    for unit, size in UNITS:
        assert get_dimen(
                f"3true{unit}q",
                state=s,
                )==size*3

def test_dimen_texbook_p57_1():
    assert get_dimen("3 inq")==14208858

def test_dimen_texbook_p57_2():
    assert get_dimen("-.013837inq")==-65535

def test_dimen_texbook_p57_3():
    assert get_dimen("0.mmq")==0

def test_dimen_texbook_p57_4():
    assert get_dimen("29 pcq")==22806528

def test_dimen_texbook_p57_5():
    assert get_dimen("+ 42,1 ddq")==2952220

def test_dimen_texbook_p57_6():
    assert get_dimen("123456789spq")==123456789

def test_dimen_font_based_unit():

    s = State()

    assert int(get_dimen(
            f"3emq",
            state=s,
            )/65536)==30

    assert int(get_dimen(
            f"3exq",
            state=s,
            )/65536)==12

def test_special_dimen():
    assert get_dimen(r"\prevdepth q")==0
    assert get_dimen(r"\pagegoal q")==0
    assert get_dimen(r"\pagetotal q")==0
    assert get_dimen(r"\pagestretch q")==0
    assert get_dimen(r"\pagefilstretch q")==0
    assert get_dimen(r"\pagefillstretch q")==0
    assert get_dimen(r"\pagefilllstretch q")==0
    assert get_dimen(r"\pageshrink q")==0
    assert get_dimen(r"\pagedepth q")==0

def test_dimen_literal_unit():
    d = Dimen(12)
    assert d.value==12

    d = Dimen(12, "pt")
    assert d.value==12*65536

    with pytest.raises(mex.exception.ParseError):
        d = Dimen(12, "spong")

def test_lastkern():
    assert get_dimen(r"\lastkern q")==0

def test_dimen_with_number():
    s = State()
    s['dimen23'] = mex.value.Dimen(3, 'pt')
    assert get_dimen(r"\dimen23 q", s,
            raw=True)==mex.value.Dimen(3, "pt")

def test_boxdimen_with_number():
    s = State()
    s['box23'] = mex.box.Box(
            width=mex.value.Dimen(10,'pt'),
            height=mex.value.Dimen(20, 'pt'),
            depth=mex.value.Dimen(30, 'pt')
            )

    for dimension, expected in [
            ('wd', '10pt'),
            ('ht', '20pt'),
            ('dp', '30pt'),
            ]:
        assert run_code(fr"\the\{dimension}23",
                state=s,
                find='chars',
                )==expected

def test_factor_then_dimen():
    s = State()
    s['dimen23'] = Dimen(42, 'pt')
    result = get_dimen(r'2\dimen23 q',
            s,
            raw=True)
    assert isinstance(result, Dimen)
    assert result==Dimen(84, 'pt')

def test_arithmetic_add_dimen():

    dimens = []

    for n in ['1sp', '7sp']:
        with expander_on_string(n) as e:
            dimens.append(Number(e))

    assert dimens[0].value==1
    assert dimens[1].value==7

    dimens[0] += dimens[1]
    assert dimens[0].value==8

def test_dimen_with_name_of_other_dimen():

    state = State()
    string = r'\dimen1=100mm \dimen2=\dimen1'

    run_code(string, state=state)

    assert str(state['dimen1'].value)== \
            str(state['dimen2'].value)

def test_dimen_eq():
    a = get_dimen('42ptq', raw=True)
    b = get_dimen('42ptq', raw=True)
    c = get_dimen('99ptq', raw=True)

    for x in [a, b, c]:
        assert isinstance(x, mex.value.Dimen)

    assert a==b
    assert a!=c
    assert b!=c

def test_dimen_cmp():
    d2mm = get_dimen('d2mmq', raw=True)
    d2cm = get_dimen('d2cmq', raw=True)
    d2in = get_dimen('d2inq', raw=True)

    for x in [d2mm, d2cm, d2in]:
        assert isinstance(x, mex.value.Dimen)

    assert d2mm<d2cm
    assert d2mm<d2in
    assert d2cm<d2in

    assert d2mm<=d2cm
    assert d2mm<=d2in
    assert d2cm<=d2in

    assert d2in>=d2cm
    assert d2in>=d2mm
    assert d2cm>=d2mm

    assert d2mm!=d2cm
    assert d2mm!=d2in
    assert d2cm!=d2in

def test_dimen_with_no_unit():
    with pytest.raises(mex.exception.ParseError):
        get_dimen("123")
