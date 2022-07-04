import io
import pytest
import copy
from yex.document import Document
from yex.value import Number, Dimen, Glue
import yex.exception
from .. import *
import yex.box
import logging

logger = logging.getLogger('yex.general')

################################

UNITS = [(unit, size/65536) for (unit, size) in [
        ("pt", 65536),
        ("pc", 786432),
        ("in", 4736286),
        ("bp", 65782),
        ("cm", 1864680),
        ("mm", 186468),
        ("dd", 70124),
        ("cc", 841489),
        ("sp", 1),
        ]]

def test_dimen_physical_unit():
    for unit, size in UNITS:
        assert get_dimen(f"3{unit}q") == size*3, unit

def test_dimen_physical_unit_true():

    s = Document()

    for unit, size in UNITS:
        assert get_dimen(
                f"3{unit}q",
                doc=s,
                )==size*3, unit

    for unit, size in UNITS:
        assert get_dimen(
                f"3true{unit}q",
                doc=s,
                )==size*3, unit

    s.begin_group()
    s[r'\mag'] = 2000
    for unit, size in UNITS:
        assert get_dimen(
                f"3{unit}q",
                doc=s,
                )==size*6, unit

    for unit, size in UNITS:
        assert get_dimen(
                f"3true{unit}q",
                doc=s,
                )==size*3, unit

    s.end_group()
    for unit, size in UNITS:
        assert get_dimen(
                f"3{unit}q",
                doc=s,
                )==size*3, unit

    for unit, size in UNITS:
        assert get_dimen(
                f"3true{unit}q",
                doc=s,
                )==size*3, unit

def test_dimen_p57_1():
    assert get_dimen("3 inq").value==14208858

def test_dimen_p57_2():
    assert get_dimen("-.013837inq").value==-65535

def test_dimen_p57_3():
    assert get_dimen("0.mmq").value==0

def test_dimen_p57_4():
    assert get_dimen("29 pcq").value==22806528

def test_dimen_p57_5():
    assert get_dimen("+ 42,1 ddq").value==2952220

def test_dimen_p57_6():
    assert get_dimen("123456789spq").value==123456789

def test_dimen_font_based_unit():

    s = Document()

    assert int(get_dimen(
            f"3emq",
            doc=s,
            ))==30

    assert int(get_dimen(
            f"3exq",
            doc=s,
            ))==12

def test_special_dimen():
    assert get_dimen(r"\prevdepth q")==-1000
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
    assert d==12

    d = Dimen(12, "pt")
    assert d==12

    with pytest.raises(yex.exception.ParseError):
        d = Dimen(12, "spong")

def test_lastkern():
    assert get_dimen(r"\lastkern q")==0

def test_dimen_with_number():
    s = Document()
    s[r'\dimen23'] = yex.value.Dimen(3, 'pt')
    assert get_dimen(r"\dimen23 q", s)==yex.value.Dimen(3, "pt")
    assert get_dimen(r"\dimen23 q", s)==3

def test_boxdimen_with_number():
    s = Document()
    s[r'\box23'] = yex.box.Box(
            width=yex.value.Dimen(10,'pt'),
            height=yex.value.Dimen(20, 'pt'),
            depth=yex.value.Dimen(30, 'pt')
            )

    for dimension, expected in [
            ('wd', '10pt'),
            ('ht', '20pt'),
            ('dp', '30pt'),
            ]:
        assert run_code(fr"\the\{dimension}23",
                doc=s,
                find='chars',
                )==expected

def test_factor_then_dimen():
    s = Document()
    s[r'\dimen23'] = Dimen(42, 'pt')
    result = get_dimen(r'2\dimen23 q',
            s)
    assert isinstance(result, Dimen)
    assert result==84

def test_arithmetic_dimens_in_place():
    # XXX "9 infinities
    # XXX "9 different unit_objs

    left = Dimen(10, 'pt')
    right = Dimen(5, 'pt')

    assert left==Dimen(10.0, 'pt')
    assert type(left.value)==int
    assert right==Dimen(5.0, 'pt')
    assert type(right.value)==int

    left += right

    assert left==Dimen(15.0, 'pt')
    assert type(left.value)==int

    left *= 2

    assert left==Dimen(30.0, 'pt')
    assert type(left.value)==int

    left /= 3

    assert left==Dimen(10.0, 'pt')
    assert type(left.value)==int

    left -= 5

    assert left==Dimen(5.0, 'pt')
    assert type(left.value)==int
    assert left==right

def test_arithmetic_dimens_not_in_place():

    left = Dimen(1, 'pt')
    right = Dimen(7, 'pt')

    assert float(right)==7.0
    assert round(right)==7.0
    assert int(right)==7

    assert left==left
    assert left!=right
    assert left<right
    assert left<=right
    assert right>left
    assert right>=left

    assert left+right == Dimen(8, 'pt')
    assert right+left == Dimen(8, 'pt')
    assert left-right == Dimen(-6, 'pt')
    assert right-left == Dimen(6, 'pt')

    assert right*2 == Dimen(14, 'pt')
    assert right*-2 == Dimen(-14, 'pt')
    assert 2*right == Dimen(14, 'pt')

    assert right/2 == Dimen(3.5, 'pt')
    assert right/-2 == Dimen(-3.5, 'pt')

    assert -left == Dimen(-1, 'pt')
    assert +left == Dimen(1, 'pt')
    assert abs(left) == Dimen(1, 'pt')

    another = Dimen(-3.5, 'pt')

    assert -another == Dimen(3.5, 'pt')
    assert +another == Dimen(-3.5, 'pt')
    assert abs(-another) == Dimen(3.5, 'pt')
    assert round(another) == Dimen(-4, 'pt')

    with pytest.raises(TypeError):
        left*right

    with pytest.raises(TypeError):
        left/right

    with pytest.raises(TypeError):
        2/right

    with pytest.raises(TypeError):
        right+2
    assert right+0 == Dimen(7, 'pt')

def test_dimen_with_name_of_other_dimen():

    doc = Document()
    string = r'\dimen1=100mm \dimen2=\dimen1'

    run_code(string, doc=doc)

    assert str(doc[r'\dimen1'].value)== \
            str(doc[r'\dimen2'].value)

def test_dimen_eq():
    a = get_dimen('42ptq')
    b = get_dimen('42ptq')
    c = get_dimen('99ptq')

    for x in [a, b, c]:
        assert isinstance(x, yex.value.Dimen)

    assert a==b
    assert a!=c
    assert b!=c

    assert a!=None
    assert not (a==None)

def test_dimen_cmp():
    d2mm = get_dimen('d2mmq')
    d2cm = get_dimen('d2cmq')
    d2in = get_dimen('d2inq')

    for x in [d2mm, d2cm, d2in]:
        assert isinstance(x, yex.value.Dimen)

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
    with pytest.raises(yex.exception.ParseError):
        get_dimen("123")

def test_dimen_deepcopy():
    # Constructed from literal
    compare_copy_and_deepcopy(Dimen(0))

    # Constructed from tokeniser
    compare_copy_and_deepcopy(get_dimen("1emq"))

def test_dimen_init_from_another_dimen():
    d1 = Dimen(2)
    d2 = Dimen.from_another(d1)

    assert d1==d2
    assert float(d1)==float(d2)
    assert d1 is not d2

def test_dimen_repr():

    d = Dimen(23, 'cm')
    assert repr(d)=='654.41pt'
    assert d.__repr__()=='654.41pt'
    assert d.__repr__(show_unit=False)=='654.41'

    d = Dimen(1, 'fil', can_use_fil=True)
    assert repr(d)=='1fil'
    assert d.__repr__()=='1fil'
    assert d.__repr__(show_unit=False)=='1fil'

def test_dimen_as_bool():

    d = Dimen(23, 'cm')
    assert d

    d = Dimen(0, 'cm')
    assert not d

def test_dimen_getstate():

    d = Dimen(23, 'sp')

    assert d.__getstate__(always_list=True)==[23, 0]
    assert d.__getstate__()==23

    d = Dimen(23, 'fil',
            can_use_fil = True,
            )

    assert d.__getstate__(always_list=True)==[23, 1]
    assert d.__getstate__()==[23, 1]

def test_dimen_pickle():

    pickle_test(
            Dimen(23, 'pt'),
            [
                (lambda v: float(v)==23,
                    'value'),
                (lambda v: v.infinity==0,
                    'infinity'),
                ],
            )

    pickle_test(
            Dimen(23, 'fill',
                can_use_fil = True,
                ),
            [
                (lambda v: float(v)==23,
                    'value'),
                (lambda v: v.infinity==2,
                    'infinity'),
                ],
            )
