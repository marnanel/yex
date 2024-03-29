import pytest
import copy
from yex.document import Document
from yex.value import Number, Dimen, Glue
import yex.exception
from test import *
import yex.put
import yex.box
import logging

logger = logging.getLogger('yex.general')

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

def test_number_containing_conditionals():

    THE_COUNT10 = r"(\the\count10)"

    assert run_code(
            setup=r"\count5=1",
            call=(
            r"\count10=10 "+
            THE_COUNT10
            ),
            find='ch',
            )=="(10)", (
                    "control: we can assign to count10"
                    )

    assert run_code(
            setup=r"\count5=0",
            call=(
                r"\count10=\ifnum\count5=1'\fi10" +
                THE_COUNT10
                ),
            find='ch',
            )=="(10)", (
                    r"\ifnum with a false condition "
                    "works between base and digits"
                    )

    assert run_code(
            setup=r"\count5=1",
            call=(
                r"\count10=\ifnum\count5=1'\fi10" +
                THE_COUNT10
                ),
            find='ch',
            )=="(8)", (
                    r"\ifnum with a true condition "
                    "works between base and digits"
                    )

    # This test sets \count10 to '101, i.e. 65, if count5==1.
    # Otherwise, it omits the central zero, giving '11, i.e. 9.
    for count5, expected, reason in [
            ('0',  '(9)', 'not taken'),
            ('1', '(65)', 'taken'),
            ]:
        assert run_code(
                setup=fr"\count5={count5}",
                call=(
                    r"\count10='1\ifnum\count5=1 0\fi 1" +
                     THE_COUNT10
                    ),
                find='ch',
                )==expected, (
                        f"Conditional between digits-- {reason}"
                        )

    with pytest.raises(yex.exception.ExpectedNumberError):
        # You can't put random other expandables after the base
        run_code(
                setup=r"\count5=1",
                call=(
                    r"\count10='\def\f{f}10" +
                     THE_COUNT10
                    ),
                find='ch',
                )

    with pytest.raises(yex.exception.ExpectedNumberError):
        # You can't put unexpandables after the base
        run_code(
                setup=r"\count5=1",
                call=(
                    r"\count10='\relax 10" +
                     THE_COUNT10
                    ),
                find='ch',
                )

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
            numbers.append(Number.from_tokens(e))

    assert numbers[0]==100
    assert numbers[1]==77

    assert (numbers[0]+numbers[1]).value==177
    assert (numbers[0]-numbers[1]).value==23

    numbers[0] += numbers[1]
    assert numbers[0]==177

    numbers[0] -= numbers[1]
    assert numbers[0]==100

    with expander_on_string('2sp') as e:
        d = Dimen.from_tokens(e)
        with pytest.raises(TypeError):
            numbers[0] += d

def test_arithmetic_multiply_divide():
    doc = Document()

    numbers = []

    for n in ['100', '100', '2']:
        with expander_on_string(n, doc=doc) as e:
            numbers.append(Number.from_tokens(e))

    with expander_on_string("2sp") as e:
        d = Dimen.from_tokens(e)

    assert [x.value for x in numbers]==[100, 100, 2]

    numbers[0] *= numbers[2]
    numbers[1] /= numbers[2]

    assert [x.value for x in numbers]==[200, 50, 2]

    # Things that shouldn't work

    with pytest.raises(TypeError): numbers[0] *= d
    with pytest.raises(TypeError): numbers[0] /= d
    with pytest.raises(yex.exception.CantMultiplyError): d *= d
    with pytest.raises(yex.exception.CantDivideError): d /= d

def test_number_from_count():
    """
    This is a regression test for a bug where calling int()
    on a count register initialised from another count register
    caused TypeError; see the commit message for why.
    """

    doc = Document()
    doc[r'\count1'] = 100

    with expander_on_string(r'\count1', doc) as t:
        n = Number.from_tokens(t)

    assert n==100
    assert int(n)==100

def test_backtick():

    doc = yex.Document()

    assert get_number(r"`Aq", doc=doc)==65, 'single character'
    assert get_number(r"`\A q", doc=doc)==65, 'control sequence of len(1)'

    with pytest.raises(yex.exception.LiteralControlTooLongError):
        get_number(r"`\Aardvark q", doc=doc)

    assert get_number(r"`\^^Kq", doc=doc)==11, 'low-ASCII single character'

    doc[r'\catcode65']=yex.parse.Token.ACTIVE
    assert doc.get('A', default=None) is None, 'A is undefined'
    assert get_number(r"`Aq", doc=doc)==65, 'undefined active character'

    run_code(
            call=r'\defA{a}',
            doc=doc,
            )

    assert doc.get('A', default=None) is not None, 'A is defined'
    assert get_number(r"`Aq", doc=doc)==65, 'undefined active character'

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

def test_number_pickle():

    n = Number(123)
    pickle_test(n,
            [
                (lambda v: (v, 123),
                    'value'),
                ],
            )

def test_number_is_immutable():
    n = Number(5)

    assert n==5
    assert n.value==5
    with pytest.raises(AttributeError):
        n.value=1234

def test_arithmetic_numbers_types():

    def run(op):
        left = Number(3)
        right = Number(5)

        result = op(left, right)

        for n in [left, right, result]:
            assert type(n)==Number
            assert type(n.value)==int
            assert type(n._value)==int

            assert result is not left
            assert result is not right

    run(lambda left, right: left+right)
    run(lambda left, right: left-right)
    run(lambda left, right: left*7)
    run(lambda left, right: left/7)
    run(lambda left, right: -left)

def test_number_multiple_points():

    def try_number(s, expected, message):

        if isinstance(expected, type) and issubclass(expected, Exception):
            with pytest.raises(expected):
                try_number(s, None, message)
        else:
            found = run_code(
                    call = (
                        fr'[\dimen10={s}]'
                        r'[\the\dimen10]'
                        ), 
                    find = 'ch',
                    )
            
            if expected is not None:
                assert found==expected, message

    try_number('1.2.3pt', yex.exception.NoUnitError, 'two full stops')
    try_number('1.2,3pt', yex.exception.NoUnitError, 'full stop then comma')
    try_number('1,2.3pt', yex.exception.NoUnitError, 'comma then full stop')
    try_number('1,2,3pt', yex.exception.NoUnitError, 'two commas')

    try_number("1.2pt", "[][1.2pt]", 'simple dimen with full stop')
    try_number("1,2pt", "[][1.2pt]", 'simple dimen with comma')

    try_number("1pt", "[][1.0pt]", 'no decimal point')
    try_number("1.0pt", "[][1.0pt]", 'point zero, with full stop')
    try_number("1,0pt", "[][1.0pt]", 'point zero, with comma')

def test_number_with_expandables_after_base():

    found = run_code(
            call=(
                r"\count10='10"
                r"\the\count10"
                ),
            find='ch',
            )
    assert found == '8', r'Control case'

    found = run_code(
            call=(
                r"\count10=\iftrue'\fi10"
                r"\the\count10"
                ),
            find='ch',
            )
    assert found == '8', r'Base marker inside \iftrue'

    found = run_code(
            call=(
                r"\count10='\iftrue\fi10"
                r"\the\count10"
                ),
            find='ch',
            )
    assert found == '8', r'Base marker before \iftrue'

    with pytest.raises(yex.exception.ExpectedNumberError):
        found = run_code(
                call=(
                    r"\count10='\relax10"
                    r"\the\count10"
                    ),
                find='ch',
                )

    with pytest.raises(yex.exception.ExpectedNumberError):
        found = run_code(
                call=(
                    r"\chardef\foo=10"
                    r"\count10='\foo"
                    ),
                find='ch',
                )
