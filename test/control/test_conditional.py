from test import *
from yex.document import Document

def test_conditional_basics(yex_test_fs):
    assert run_code(r"a\iftrue b\fi z",
            find = "chars") =='abz'
    assert run_code(r"a\iffalse b\fi z",
            find = "chars") =='az'
    assert run_code(r"a\iftrue b\else c\fi z",
            find = "chars") =='abz'
    assert run_code(r"a\iffalse b\else c\fi z",
            find = "chars") =='acz'

def test_conditional_nesting(yex_test_fs):
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

def test_conditional_ifcase(yex_test_fs):

    doc = Document()

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

def test_conditional_ifnum_irs(yex_test_fs):
    # Based on the example on p207 of the TeXbook.

    doc = Document()

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

def test_conditional_ifdim(yex_test_fs):

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

def test_conditional_ifodd(yex_test_fs):

    doc = Document()

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

def test_conditional_of_modes(yex_test_fs):

    string = (
        r"\ifvmode V\fi"
        r"\ifhmode H\fi"
        r"\ifmmode M\fi"
        r"\ifinner I\fi"
        )

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
            s = run_code(
                    fr"{control_name} {symbol}\fi",
                    mode = mode,
                    find='chars',
                    )
            found += s

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

def test_conditional_ifcat(yex_test_fs):
    doc = Document()

    assert _ifcat('11', doc)=='T'
    assert _ifcat('12', doc)=='T'
    assert _ifcat('AA', doc)=='T'
    assert _ifcat('AB', doc)=='T'
    assert _ifcat('1A', doc)=='F'
    assert _ifcat('A1', doc)=='F'

def test_conditional_ifcat_p209(yex_test_fs):
    doc = Document()

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

def test_conditional_ifproper(yex_test_fs):
    doc = Document()

    assert _ifproper('11', doc)=='T'
    assert _ifproper('12', doc)=='F'
    assert _ifproper('AA', doc)=='T'
    assert _ifproper('AB', doc)=='F'
    assert _ifproper('1A', doc)=='F'
    assert _ifproper('A1', doc)=='F'

def test_conditional_ifproper_p209(yex_test_fs):
    doc = Document()

    # Example from p209 of the TeXbook
    run_code((
        r"\def\a{*}"
        r"\let\b=*"
        r"\def\c{/}"),
        find='chars',
        doc=doc,
        )

    assert _ifproper(r"*\a", doc)=="T"
    assert _ifproper(r"\a\b", doc)=="T"
    assert _ifproper(r"\a\c", doc)=="F"
