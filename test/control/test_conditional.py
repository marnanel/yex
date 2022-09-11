from test import *
import yex
import pytest

def test_conditional_basics():
    assert run_code(r"a\iftrue b\fi z",
            find = "chars") =='abz'
    assert run_code(r"a\iffalse b\fi z",
            find = "chars") =='az'
    assert run_code(r"a\iftrue b\else c\fi z",
            find = "chars") =='abz'
    assert run_code(r"a\iffalse b\else c\fi z",
            find = "chars") =='acz'

def test_conditional_nesting():
    for outer, inner, expected in [
            ('true', 'true', 'abcez'),
            ('true', 'false', 'abdez'),
            ('false', 'true', 'afgiz'),
            ('false', 'false', 'afhiz'),
            ]:
        assert run_code((
            rf"a\if{outer} "
            rf"b\if{inner} c\else d\fi e"
            r"\else "
            rf"f\if{inner} g\else h\fi i"
            r"\fi z"),
            find='chars',
            )==expected

def test_conditional_ifcase():

    doc = yex.Document()

    run_code(r"\countdef\who=0",
            find='chars',
            doc=doc)

    for expected in ['fred', 'wilma', 'barney',
            'betty', 'betty', 'betty']:

        assert run_code((
                r"\ifcase\who fred"
                    r"\or wilma"
                    r"\or barney"
                    r"\else betty"
                    r"\fi\advance\who by 1"),
                    find='chars',
                    doc=doc,
                    )==expected

def test_conditional_ifnum_irs():
    # Based on the example on p207 of the TeXbook.

    doc = yex.Document()

    run_code(r"\countdef\balance=77",
            find='chars',
            doc=doc)

    for balance, expected in [
            (-100, 'under'),
            (0, 'fully'),
            (100, 'over'),
            ]:

        doc[r'\count77'] = balance

        assert run_code(
                r'\ifnum\balance=0 fully'
                r'\else\ifnum\balance>0 over'
                r'\else under'
                r'\fi'
                r'\fi',
                find='chars',
                doc=doc,
                )==expected

def test_conditional_ifdim():

    for length, expected in [
            ('5mm', 'shorter'),
            ('50mm', 'same'),
            ('100mm', 'longer'),
            ]:

        assert run_code(
                r"\dimen1="+length+(r"\dimen2=50mm"
                    r"\ifdim\dimen1=\dimen2 same\fi"
                    r"\ifdim\dimen1<\dimen2 shorter\fi"
                    r"\ifdim\dimen1>\dimen2 longer\fi"),
                find='chars',
                )==expected

def test_conditional_ifodd():

    doc = yex.Document()

    doc[r'\count50'] = 50
    doc[r'\count51'] = 51

    for test in [
            r'\ifodd0 N\else Y\fi',
            r'\ifodd1 Y\else N\fi',
            r'\ifodd2 N\else Y\fi',
            r'\ifodd\count50 N\else Y\fi',
            r'\ifodd\count51 Y\else N\fi',
            ]:
        assert run_code(test,
                find='chars',
                doc=doc)=="Y"

def test_conditional_of_modes():

    doc = yex.Document()

    for mode, expected in [
            ('vertical', 'V'),
            ('internal_vertical', 'VI'),
            ('horizontal', 'H'),
            ('restricted_horizontal', 'HI'),
            ('math', 'MI'),
            ('display_math', 'M'),
            ]:

        found = ''
        for control_name, symbol in [
            (r"\ifvmode", 'V'),
            (r"\ifhmode", 'H'),
            (r"\ifmmode", 'M'),
            (r"\ifinner", 'I'),
            ]:
            doc[r'\count23'] = 0
            run_code(
                    fr"{control_name}\count23=1\else\count23=0\fi",
                    mode = mode,
                    doc = doc,
                    find='chars',
                    )
            if doc[r'\count23'].value==1:
                found += symbol

        assert found==expected, f'in {mode}, wanted {expected}, got {found}'

def _ifcat(q, doc):
    r"""
    Runs \ifcat<q> on the given Document.
    Returns T if it finds True and F if it finds False.
    """
    return run_code(
            r"\ifcat " + q +
            r"T\else F\fi",
            find='chars',
            doc=doc,
            ).strip()

def test_conditional_ifcat():
    doc = yex.Document()

    assert _ifcat('11', doc)=='T'
    assert _ifcat('12', doc)=='T'
    assert _ifcat('AA', doc)=='T'
    assert _ifcat('AB', doc)=='T'
    assert _ifcat('1A', doc)=='F'
    assert _ifcat('A1', doc)=='F'

def test_conditional_ifcat_p209():
    doc = yex.Document()

    # Example from p209 of the TeXbook
    run_code(r"\catcode`[=13 \catcode`]=13 \def[{*}",
            find='chars',
            doc=doc)

    # So at this point, [ and ] are both active characters,
    # and [ has been defined to expand to *.

    assert _ifcat(r"\noexpand[\noexpand]", doc)=="T"
    assert _ifcat(r"[*", doc)=="T"
    assert _ifcat(r"\noexpand[*", doc)=="F"

def _ifproper(q, doc):
    r"""
    Runs \if <q> on the given Document.
    Returns T if it finds True and F if it finds False.
    """
    return run_code(
            r"\if " + q +
            r" T\else F\fi",
            find='chars',
            doc=doc)

def test_conditional_ifproper():
    doc = yex.Document()

    assert _ifproper('11', doc)=='T'
    assert _ifproper('12', doc)=='F'
    assert _ifproper('AA', doc)=='T'
    assert _ifproper('AB', doc)=='F'
    assert _ifproper('1A', doc)=='F'
    assert _ifproper('A1', doc)=='F'

def test_conditional_ifproper_p209():
    doc = yex.Document()

    # Example from p209 of the TeXbook
    run_code((
        r"\def\a{*}"
        r"\let\b=*"
        r"\def\c{/}"),
        doc=doc,
        )

    assert _ifproper(r"*\a", doc)=="T"
    assert _ifproper(r"\a\b", doc)=="T"
    assert _ifproper(r"\a\c", doc)=="F"

def _run_ifx_test(c1, c2, doc=None, setup=None):
    found = run_code(
            doc=doc,
            setup=setup,
            call=fr'\ifx{c1}{c2}1\else 0\fi',
            find='ch',
            )
    if found=='0':
        return False
    elif found=='1':
        return True
    else:
        raise ValueError(f"found: {found}")

def test_conditional_ifx_token():
    doc = yex.Document()

    t = yex.parse.Tokeniser(doc, '')
    e = yex.parse.Expander(t)

    def compare_pair(left_char, left_cat, right_char, right_cat):

        left = yex.parse.get_token(
                ch = left_char,
                category = left_cat,
                )

        right = yex.parse.get_token(
                ch = right_char,
                category = right_cat,
                )

        e.push(r'1\else 0\fi')
        e.push(right)
        e.push(left)
        e.push(r'\ifx')
        result = e.next(level='executing')

        if result.ch=='0':
            return False
        elif result.ch=='1':
            return True
        else:
            raise ValueError(f"found: {found}")

    assert compare_pair('A', 11, 'A', 11)==True
    assert compare_pair('A', 12, 'A', 11)==False
    assert compare_pair('A', 11, 'B', 11)==False
    assert compare_pair('A', 12, 'B', 11)==False

def test_conditional_ifx_primitive():
    assert _run_ifx_test(r'\if', r'\if')==True
    assert _run_ifx_test(r'\if', r'\ifx')==False
    assert _run_ifx_test(r'\ifx', r'\if')==False
    assert _run_ifx_test(r'\ifx', r'\ifx')==True

def test_conditional_ifx_font():
    assert _run_ifx_test(r'\nullfont', r'\nullfont')==True

def test_conditional_ifx_chardef_countdef():

    for kind in ['chardef', 'countdef']:
        doc = yex.Document()
        run_code(
                fr'\{kind}\fred=1\{kind}\barney=2'
                fr'\{kind}\wilma=1\let\betty=\fred',
                doc=doc,
                )

        assert _run_ifx_test(r'\fred', r'\fred',   doc=doc)==True
        assert _run_ifx_test(r'\fred', r'\barney', doc=doc)==False
        assert _run_ifx_test(r'\fred', r'\wilma',  doc=doc)==True
        assert _run_ifx_test(r'\fred', r'\betty',  doc=doc)==True

def test_conditional_ifx_disparate():
    assert _run_ifx_test(r'\ifx', r'1')==False
    assert _run_ifx_test(r'\ifx', r'\nullfont')==False

def test_conditional_ifx_macro_status():
    doc = yex.Document()

    run_code(call=(
            r'\def\aa{}'
            r'\def\ab{}'
            r'\long\def\ba{}'
            r'\long\def\bb{}'
            r'\outer\def\ca{}'
            r'\outer\def\cb{}'
            r'\outer\long\def\da{}'
            r'\outer\long\def\db{}'
            ),
            doc=doc,
            )

    assert _run_ifx_test(r'\aa', r'\ab', doc=doc)==True
    assert _run_ifx_test(r'\aa', r'\ba', doc=doc)==False
    assert _run_ifx_test(r'\aa', r'\ca', doc=doc)==False
    assert _run_ifx_test(r'\aa', r'\da', doc=doc)==False

    assert _run_ifx_test(r'\ba', r'\bb', doc=doc)==True
    assert _run_ifx_test(r'\ba', r'\ca', doc=doc)==False
    assert _run_ifx_test(r'\ba', r'\da', doc=doc)==False

    assert _run_ifx_test(r'\ca', r'\cb', doc=doc)==True
    assert _run_ifx_test(r'\ca', r'\da', doc=doc)==False

    assert _run_ifx_test(r'\da', r'\db', doc=doc)==True

def test_conditional_ifx_p209_expansions():

    doc = yex.Document()

    SETUP = (
            r'\def\a{\c}'
            r'\def\b{\d}'
            r'\def\c{\e}'
            r'\def\d{\e}'
            r'\def\e{A}'
            )

    run_code(
            call=SETUP,
            doc=doc,
            )

    assert _run_ifx_test(r'\a', r'\b', doc=doc)==False
    assert _run_ifx_test(r'\a', r'\c', doc=doc)==False
    assert _run_ifx_test(r'\a', r'\d', doc=doc)==False
    assert _run_ifx_test(r'\a', r'\e', doc=doc)==False

    assert _run_ifx_test(r'\b', r'\c', doc=doc)==False
    assert _run_ifx_test(r'\b', r'\d', doc=doc)==False
    assert _run_ifx_test(r'\b', r'\e', doc=doc)==False

    assert _run_ifx_test(r'\c', r'\d', doc=doc)==True
    assert _run_ifx_test(r'\c', r'\e', doc=doc)==False

    assert _run_ifx_test(r'\d', r'\e', doc=doc)==False

def test_conditional_ifeof(fs):

    FILENAME = 'wombat.txt'
    TEST_STRING = 'Hurrah for wombats\r'

    doc = yex.Document()

    def run_ifeof_test(expected):
        found = run_code(r"a\ifeof1 b\fi z",
                doc=doc,
                find = "chars") =='abz'
        assert expected == found

    with open(FILENAME, 'w') as wombat:
        wombat.write(TEST_STRING)

    run_ifeof_test(expected=True) # closed streams are always True

    with doc['input_streams;1'].open(FILENAME) as input1:
        assert input_stream.at_eof == False
        run_ifeof_test(expected=False)

        assert input_stream.read() == TEST_STRING

        assert input_stream.at_eof == True
        run_ifeof_test(expected=True)
