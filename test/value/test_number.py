import io
import pytest
from mex.state import State
from mex.parse import Token, Tokeniser, Expander
from mex.value import Number, Dimen, Glue
import mex.exception
from .. import *
import mex.put
import mex.box
import logging

general_logger = logging.getLogger('mex.general')

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

def test_number_eq():
    a = get_number('42q', raw=True)
    b = get_number('42q', raw=True)
    c = get_number('99q', raw=True)

    for x in [a, b, c]:
        assert isinstance(x, mex.value.Number)

    assert a==b
    assert a!=c
    assert b!=c

    assert a==42
    assert a!=99

    assert c==99
    assert c!=42

def test_number_cmp():
    n42 = get_number('42q', raw=True)
    n52 = get_number('52q', raw=True)
    n90 = get_number('90q', raw=True)

    for x in [n42, n52, n90]:
        assert isinstance(x, mex.value.Number)

    assert n42<n52
    assert n52>n42
    assert n42<=n52
    assert n52>=n42
    assert n42!=n52

def test_number_internal_integer():
    assert get_number('\\count1q')==0

def test_number_internal_dimen():
    s = State()
    s['hsize'] = mex.value.Dimen(100, 'pt')
    assert get_number('\\hsize q', s)==65536 * 100
    assert get_dimen('\\hsize q', s)==65536.0 * 100

def test_number_internal_glue():
    s = State()
    s['skip100'] = mex.value.Glue(100, 'pt')
    print(get_glue('\\skip100 q', s))
    assert get_number('\\skip100 q', s)==65536 * 100
    assert get_glue('\\skip100 q', s)==(
            6553600.0, 0.0, 0.0, 0, 0)

def test_special_integer():
    assert get_number('\\spacefactor q')==1000
    assert get_number('\\prevgraf q')==0
    assert get_number('\\deadcycles q')==0
    assert get_number('\\insertpenalties q')==0

def test_lastpenalty():
    assert get_number('\\lastpenalty q')==0

def test_count_with_number():
    s = State()
    s['count23'] = 234
    assert get_number('\\count23q', s)==234

def test_codename_with_number():
    assert get_number('\\catcode65q')==11 # "A" == letter
    assert get_number('\\mathcode65q')==0x7100+65
    assert get_number('\\sfcode23q')==1000
    assert get_number('\\sfcode65q')==999
    assert get_number('\\delcode23q')==-1
    assert get_number('\\delcode46q')==0

def test_upper_and_lower_case():
    assert get_number('\\lccode65q')==ord('a')
    assert get_number('\\uccode65q')==ord('A')

    assert get_number('\\lccode97q')==ord('a')
    assert get_number('\\uccode97q')==ord('A')

def test_set_upper_and_lower_case():
    for n, original in [('lccode', ord('a')), ('uccode', 65)]:
        s = State()
        assert get_number(f'\\{n}65q', s)==original
        s[f'{n}65'] = 40
        assert get_number(f'\\{n}65q', s)==40
        s[f'{n}65'] = 50
        assert get_number(f'\\{n}65q', s)==50

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
