import io
import pytest
from mex.state import State
from mex.token import Token, Tokeniser
from mex.value import Number, Dimen

def _get_number(number):
    """
    Creates a State and a Tokeniser, and tokenises the string
    you pass in. The string should represent a number followed
    by the letter "q" (so we can test how well numbers are
    delimited by the following characters).

    Returns the number.
    """

    s = State()
    t = Tokeniser(s)

    with io.StringIO(number) as f:
        tokens = t.read(f)

        result = Number(t, tokens)

        try:
            q = tokens.__next__()
        except StopIteration:
            raise ValueError("Wanted trailing 'q' for "
                    f"{number} but found nothing")

        if q.category==q.LETTER and q.ch=='q':
            return result.value
        else:
            raise ValueError(f"Wanted trailing 'q' for "
                    f"{number} but found {q}")

def _get_dimen(dimen):
    """
    Creates a State and a Tokeniser, and tokenises the string
    you pass in. The string should represent a dimen followed
    by the letter "q" (so we can test how well numbers are
    delimited by the following characters).

    Returns the size in millimetres.
    """

    s = State()
    t = Tokeniser(s)

    with io.StringIO(dimen) as f:
        tokens = t.read(f)

        result = Dimen(t, tokens)

        try:
            q = tokens.__next__()
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
    assert _get_number('\\count1 q')==0

@pytest.mark.xfail
def test_number_internal_dimen():
    assert _get_number('\\hsize q')==0

@pytest.mark.xfail
def test_number_internal_glue():
    assert _get_number('\\skip100 q')==0

#################################

def test_dimen_physical_unit():
    assert _get_dimen("3pcq")==2359296
    assert _get_dimen("3ptq")==196608
    assert _get_dimen("3inq")==14208858
    assert _get_dimen("3bpq")==197346
    assert _get_dimen("3cmq")==5594040
    assert _get_dimen("3mmq")==559404
    assert _get_dimen("3ddq")==210372
    assert _get_dimen("3ccq")==2524467
    assert _get_dimen("3spq")==3

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
