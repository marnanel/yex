import pytest
import copy
from yex.document import Document
from yex.value import Number, Dimen, Glue
import yex.exception
from .. import *
import yex.put
import yex.box
import logging

general_logger = logging.getLogger('yex.general')

def test_number_decimal():
    assert get_number('42q')==42

def test_number_octal():
    assert get_number("'52q")==42

def test_number_hex():
    assert get_number('"2aq')==42

def test_number_char():
    assert get_number('`*q')==42

def test_number_control():
    assert get_number('`\\{q')==123

def test_number_decimal_negative():
    assert get_number('-42q')==-42

def test_number_octal_negative():
    assert get_number("-'52q")==-42

def test_number_hex_negative():
    assert get_number('-"2aq')==-42

def test_number_decimal_positive():
    assert get_number('+42q')==42

def test_number_decimal_double_negative():
    assert get_number('--42q')==42

def test_number_constructed_from_float():

    # A number can be constructed from a float, but
    # the float is rounded. So this should be equal to 2.

    a = Number(2.5)
    assert a==2

    # (Don't assert that a==2.5; we round the other argument too.)

    # And if you add it to itself, it's 4 and not 5.
    assert a+a==4

    c = get_number('2q', raw=True)
    assert a+c==4, ('Numbers constructed from floats can be added to '
            'Numbers constructed from tokens')

def test_number_eq():
    a = get_number('42q', raw=True)
    b = get_number('42q', raw=True)
    c = get_number('99q', raw=True)

    for x in [a, b, c]:
        assert isinstance(x, yex.value.Number)

    assert a==b
    assert a!=c
    assert b!=c

    assert a==42
    assert a!=99

    assert c==99
    assert c!=42

    assert a!=None
    assert not (a==None)

def test_number_cmp():
    n42 = get_number('42q', raw=True)
    n52 = get_number('52q', raw=True)
    n90 = get_number('90q', raw=True)

    for x in [n42, n52, n90]:
        assert isinstance(x, yex.value.Number)

    assert n42<n52
    assert n52>n42
    assert n42<=n52
    assert n52>=n42
    assert n42!=n52

def test_number_internal_integer():
    assert get_number(r'\count1q')==0

def test_number_internal_dimen():
    s = Document()
    s[r'\hsize'] = yex.value.Dimen(100, 'pt')
    assert get_number(r'\hsize q', s)==100
    assert get_dimen(r'\hsize q', s)==Dimen(100, 'pt')

def test_number_internal_glue():
    s = Document()
    s[r'\skip100'] = yex.value.Glue(100, 'pt')
    print(get_glue(r'\skip100 q', s))
    assert get_number(r'\skip100 q', s)==100
    assert get_glue(r'\skip100 q', s)==(
            100.0, 0.0, 0.0, 0, 0)

def test_special_integer():
    assert get_number(r'\spacefactor q')==1000
    assert get_number(r'\prevgraf q')==0
    assert get_number(r'\deadcycles q')==0
    assert get_number(r'\insertpenalties q')==0

def test_lastpenalty():
    assert get_number(r'\lastpenalty q')==0

def test_count_with_number():
    s = Document()
    s[r'\count23'] = 234
    assert get_number(r'\count23q', s)==234

def test_codename_with_number():
    assert get_number(r'\catcode65q')==11 # "A" == letter
    assert get_number(r'\mathcode65q')==0x7100+65
    assert get_number(r'\sfcode23q')==1000
    assert get_number(r'\sfcode65q')==999
    assert get_number(r'\delcode23q')==-1
    assert get_number(r'\delcode46q')==0

def test_upper_and_lower_case():
    assert get_number(r'\lccode65q')==ord('a')
    assert get_number(r'\uccode65q')==ord('A')

    assert get_number(r'\lccode97q')==ord('a')
    assert get_number(r'\uccode97q')==ord('A')

def test_set_upper_and_lower_case():
    for n, original in [('lccode', ord('a')), ('uccode', 65)]:
        s = Document()
        assert get_number(f'\\{n}65q', s)==original
        s[fr'\{n}65'] = 40
        assert get_number(f'\\{n}65q', s)==40
        s[fr'\{n}65'] = 50
        assert get_number(f'\\{n}65q', s)==50

def test_arithmetic_add_count():
    doc = Document()

    numbers = []

    for n in ['100', '77']:
        with expander_on_string(n, doc=doc) as e:
            numbers.append(Number(e))

    assert numbers[0].value==100
    assert numbers[1].value==77

    assert (numbers[0]+numbers[1]).value==177
    assert (numbers[0]-numbers[1]).value==23

    numbers[0] += numbers[1]
    assert numbers[0].value==177

    numbers[0] -= numbers[1]
    assert numbers[0].value==100

    with expander_on_string('2sp') as e:
        d = Dimen(e)
        with pytest.raises(TypeError):
            numbers[0] += d

def test_arithmetic_multiply_divide():
    doc = Document()

    numbers = []

    for n in ['100', '100', '2']:
        with expander_on_string(n, doc=doc) as e:
            numbers.append(Number(e))

    with expander_on_string("2sp") as e:
        d = Dimen(e)

    assert [x.value for x in numbers]==[100, 100, 2]

    numbers[0] *= numbers[2]
    numbers[1] /= numbers[2]

    assert [x.value for x in numbers]==[200, 50, 2]

    # Things that shouldn't work

    with pytest.raises(TypeError): numbers[0] *= d
    with pytest.raises(TypeError): numbers[0] /= d
    with pytest.raises(TypeError): d *= d
    with pytest.raises(TypeError): d /= d

def test_number_from_count():
    """
    This is a regression test for a bug where calling int()
    on a count register initialised from another count register
    caused TypeError; see the commit message for why.
    """

    doc = Document()
    doc[r'\count1'] = 100

    with expander_on_string(r'\count1', doc) as t:
        n = Number(t)

    assert n==100
    assert int(n)==100

def test_backtick():
    assert get_number(r"`Aq")==65
    assert get_number(r"`\A q")==65

    assert get_number(r"`\^^Kq")==11

    # XXX What if the single-character control symbol is defined?

def test_number_is_chardef():

    s = Document()

    run_code(r"\chardef\active=13 \catcode`\~=\active",
            doc=s)

    assert s[r'\catcode126']==13

def test_number_deepcopy():
    a = [Number(0)]
    b = copy.copy(a)

    assert a[0] is b[0]

    c = copy.deepcopy(a)

    assert a[0] is not c[0]

def test_number_no_args():
    a = Number(0)
    b = Number(1)
    c = Number()

    assert a!=b
    assert a==c
    assert b!=c

def test_number_deepcopy():
    # Constructed from literal
    compare_copy_and_deepcopy(Number(0))

    # Constructed from tokeniser
    compare_copy_and_deepcopy(get_number("0q", raw=True))
