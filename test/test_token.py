import io
import pytest
from mex.state import State
from mex.token import Token, Tokeniser
from mex.macro import Number, Dimen

def test_token_simple_create():
    t = Token('q', 0)
    assert t is not None

def test_token_cats():

    categories = [
            'Escape character',
            'Beginning of group',
            'End of group',
            'Math shift',
            'Alignment tab',
            'End of line',
            'Parameter',
            'Superscript',
            'Subscript',
            'Ignored character',
            'Space',
            'Letter',
            'Other character',
            'Active character',
            'Comment character',
            'Invalid character',
            ]

    for i in range(16):
        t = Token(
                ch = chr(i+32),
                category = i)
        assert ord(t.ch) == i+32
        assert t.category == i
        assert t.meaning == categories[i]

def test_tokeniser_simple_create():
    s = State()
    t = Tokeniser(s)
    assert t is not None

def _test_tokeniser(
        text,
        expected,
        ):
    s = State()
    t = Tokeniser(s)

    result = [
            ]

    with io.StringIO(text) as f:

        for item in t.read(f):
            result.append(item.__str__())

    assert result == expected
    return result

def test_tokeniser_simple_text():

    _test_tokeniser(
            text = """
    fred
    """,
    expected = [
        '    10     End of line',
        '    32 ( ) Space',
        '    32 ( ) Space',
        '    32 ( ) Space',
        '    32 ( ) Space',
        '   102 (f) Letter',
        '   114 (r) Letter',
        '   101 (e) Letter',
        '   100 (d) Letter',
        '    10     End of line',
        '    32 ( ) Space',
        '    32 ( ) Space',
        '    32 ( ) Space',
        '    32 ( ) Space',
        ],
    )

def test_tokeniser_push_back():
    _test_tokeniser(
            text = "\\loop\\iftrue",
    expected = [
        '\\loop',
        '\\iftrue',
        ],
    )

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

@pytest.mark.xfail
def test_dimen_pc():
    assert _get_dimen("3pcq")==3

@pytest.mark.xfail
def test_dimen_pt():
    assert _get_dimen("3ptq")==3

@pytest.mark.xfail
def test_dimen_in():
    assert _get_dimen("3inq")==3

@pytest.mark.xfail
def test_dimen_bp():
    assert _get_dimen("3bpq")==3

@pytest.mark.xfail
def test_dimen_cm():
    assert _get_dimen("3cmq")==3

@pytest.mark.xfail
def test_dimen_mm():
    assert _get_dimen("3mmq")==3

@pytest.mark.xfail
def test_dimen_dd():
    assert _get_dimen("3ddq")==3

@pytest.mark.xfail
def test_dimen_cc():
    assert _get_dimen("3ccq")==3

@pytest.mark.xfail
def test_dimen_sp():
    assert _get_dimen("3spq")==3

@pytest.mark.xfail
def test_dimen_texbook_p57_1():
    assert _get_dimen("3 inq")==3

@pytest.mark.xfail
def test_dimen_texbook_p57_2():
    assert _get_dimen("-.013837inq")==3

@pytest.mark.xfail
def test_dimen_texbook_p57_3():
    assert _get_dimen("0.mmq")==0

@pytest.mark.xfail
def test_dimen_texbook_p57_4():
    assert _get_dimen("29 pcq")==3

@pytest.mark.xfail
def test_dimen_texbook_p57_5():
    assert _get_dimen("+ 42,1 ddq")==3

@pytest.mark.xfail
def test_dimen_texbook_p57_6():
    assert _get_dimen("123456789spq")==3
