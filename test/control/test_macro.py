import io
import pytest
from yex.document import Document
from .. import *
import yex.font
import yex.put

def test_expand_simple():
    string = "This is a test"
    assert run_code(string,
            find = 'chars',
            ) == string

def test_expand_simple_def():
    assert run_code(
            setup = r'\def\wombat{Wombat}',
            call = r'\wombat',
            find = "chars",
            ) =="Wombat"

def test_expand_simple_with_nested_braces():
    string = "\\def\\wombat{Wom{b}at}\\wombat"
    assert run_code(
            string,
            find = "chars",
            ) =="Wom{b}at"

def test_expand_active_character():
    assert run_code(
            r"\catcode`X=13\def X{your}This is X life",
            find = "chars",
            ) =="This is your life"

def test_expand_with_single():
    assert run_code(r"This is a test",
            single=False,
            find = "chars") =="This is a test"

    assert run_code(r"This is a test",
            single=True,
            find = "chars") =="T"

    assert run_code(r"{This is} a test",
            single=False,
            find = "chars") =="{This is} a test"

    assert run_code(r"{This is} a test",
            single=True,
            find = "chars") =="This is"

    assert run_code(r"{Thi{s} is} a test",
            single=False,
            find = "chars") =="{Thi{s} is} a test"

    assert run_code(r"{Thi{s} is} a test",
            single=True,
            find = "chars") =="Thi{s} is"

def test_expand_with_level_and_single():
    assert run_code(r"{\def\wombat{x}\wombat} a test",
            single=True, level='expanding',
            find = "ch") ==r"x"
    assert run_code(r"{\def\wombat{x}\wombat} a test",
            single=True, level='reading',
            find = "ch") ==r"\def\wombatx"

def test_expand_with_run_code():

    assert run_code(r"abc",
            find = "ch") == 'abc'

    assert run_code(r"\def\wombat{x}\wombat",
            find = "ch") == 'x'

    assert run_code(r"\def\wombat{x}\wombat\wombat\wombat",
            find = 'ch') == 'xxx'

def test_expand_ex_20_2():
    string = r"\def\a{\b}" +\
            r"\def\b{A\def\a{B\def\a{C\def\a{\b}}}}" +\
            r"\def\puzzle{\a\a\a\a\a}" +\
            r"\puzzle"
    assert run_code(string,
            find = "chars") =="ABCAB"

def test_expand_params_p200():
    # I've replaced \\ldots with ... because it's not
    # pre-defined here, and _ with - because it's run
    # in vertical mode.
    string = r"\def\row#1{(#1-1,...,#1-n)}\row x"
    assert run_code(string,
            find = "chars") ==r"(x-1,...,x-n)"

def test_expand_params_p201():
    # I've replaced \\ldots with ... because it's not
    # pre-defined here, and _ with - because it's run
    # in vertical mode.
    string = r"\def\row#1#2{(#1-1,...,#1-#2)}\row xn"
    assert run_code(string,
            find = "chars") ==r"(x-1,...,x-n)"

def test_expand_params_p203():
    assert run_code(
            setup=(
                r"\def\cs AB#1#2C$#3\$ {#3{ab#1}#1 c##\x #2}"
                ),
            call=(
                r"\cs AB {\Look}C${And\$ }{look}\$ 5"
                ),
            find='ch',
            mode='dummy',
            )==r"{And\$ }{look}{ab\Look}\Look c#\x5"

def test_expand_params_p325():
    string = (
            r"\def\a#1{\def\b##1{##1#1}}"
            r"\a!"
            r"\b x"
            )
    assert run_code(string,
            find='chars',
            )=="x!"

def test_expand_params_final_hash_p204():
    # The output "\hboxto" is an artefact of run_code;
    # it just concats all the string representations.
    assert run_code(
            setup=(
                r"\def\a#1#{\qbox to #1}"
                ),
            call=(
                r"\a3pt{x}"
                ),
            find='ch',
            mode='dummy',
            )==r"\qboxto 3pt{x}"

def test_expand_params_out_of_order():
    with pytest.raises(yex.exception.ParseError):
        string = r"\def\cs#2#1{foo}"
        run_code(string,
                find='chars',
                )

def test_expand_params_basic_shortargument():
    string = "\\def\\hello#1{a#1b}\\hello 1"
    assert run_code(string,
            find = "chars") =="a1b"

def test_expand_params_basic_longargument():
    string = "\\def\\hello#1{a#1b}\\hello {world}"
    assert run_code(string,
            find = "chars") =="aworldb"

def test_expand_params_with_delimiters():
    string = (
            r"\def\cs#1wombat#2spong{#2#1}"
            r"\cs wombawombatsposponspong"
            )
    assert run_code(string,
            find = "chars") =="sposponwomba"

def test_expand_params_with_prefix():
    string = (
            r"\def\cs wombat#1{#1e}"
            r"\cs wombat{spong}wombat"
            )
    assert run_code(string,
            find = "chars") =="spongewombat"

    string = (
            r"\def\cs wombat#1wombat{#1e}"
            r"\cs wombatswombatspong"
            )
    assert run_code(string,
            find = "chars") =="sespong"

    string = (
            r"\def\cs wombat#1wombat{#1e}"
            r"\cs wombatspongwombat"
            )
    assert run_code(string,
            find = "chars") =="sponge"

    with pytest.raises(yex.exception.MacroError):
        string = (
                r"\def\cs wombat#1wombat{#1e}"
                r"\cs womspong"
                )
        run_code(string)

def test_expand_params_non_numeric():
    for forbidden in [
            '!',
            'A',
            r'\q',
            ]:
        with pytest.raises(yex.exception.ParseError):
            string = (
                    r"\def\wombat#"
                    f"{forbidden}"
                    r"{hello}"
                    )
            run_code(string,
                    find='chars',
                    )

def test_expand_long_def():
    doc = Document()

    run_code(r"\long\def\ab#1{a#1b}",
            doc=doc)
    run_code(r"\def\cd#1{c#1d}",
            doc=doc)

    assert doc[r'\ab'].is_long == True
    assert run_code(r"\ab z",
            doc=doc,
            find='ch',
            )=="azb"
    assert run_code(r"\ab \par",
            doc=doc,
            find='ch',
            )==r"a\parb"

    assert doc[r'\cd'].is_long == False
    assert run_code(r"\cd z",
            doc=doc,
            find='ch',
            )=="czd"
    with pytest.raises(yex.exception.ParseError):
        run_code(r"\cd \par",
                doc=doc,
                find='ch',
                )

def test_expand_outer():

    # Per the TeXbook, p.205, \outer macros may not appear
    # in several places. We don't test all of them yet
    # (marked with a *), but we will. (TODO.) They are:
    #
    #  - In a macro argument
    #  - Param text of definition *
    #  - Replacement text of definition
    #  - Preamble to alignment *
    #  - Conditional text which is being skipped over *

    SETUP = (
            r"\outer\def\wombat{W}"
            r"\def\notwombat{W}"
            r"\def\spong#1{Spong}"
            )

    doc = Document()
    run_code(SETUP,
            doc=doc)

    assert doc[r'\wombat'].is_outer == True
    assert doc[r'\notwombat'].is_outer == False

    ##############################

    for (forbidden, context) in [
            (
                r'\spong{%s}',
                'macro argument',
                ),
            (
                r'\def\fred#1%s#2{fred}',
                'param text',
                ),
            (
                r'\def\fred#1{fred#1}\fred %s',
                'replacement text',
                ),
            ]:

        try:
            reason = f"outer macro called in {context}"
            run_code(
                    setup = SETUP,
                    call = forbidden % (r'\wombat',),
                    find = 'chars',
                    # not reusing doc
                    )
            assert False, reason + " succeeded"
        except yex.exception.YexError:
            assert True, reason + " failed"

    ##############################

        try:
            reason = f'non-outer called in {context}'
            run_code(
                    setup = SETUP,
                    call = forbidden % (r'\notwombat',),
                    find = 'chars',
                    )
            assert True, reason + " succeeded"
        except yex.exception.YexError:
            assert False, reason + " failed"

def test_expand_edef_p214():

    assert run_code(
            setup=(
                r'\def\double#1{#1#1}'
                r'\edef\a{\double{xy}}'
                ),
            call=(
                r"\a"
                ),
            find='chars',
            )=='xy'*2

    assert run_code(
            setup=(
                r'\def\double#1{#1#1}'
                r'\edef\a{\double{xy}}'
                r'\edef\a{\double\a}\a'
                ),
            call=(
                r"\a"
                ),
            find='chars',
            )=='xy'*4

def test_expand_long_long_long_def_flag():
    doc = Document()
    string = "\\long\\long\\long\\def\\wombat{Wombat}\\wombat"
    assert run_code(string,
            find='chars',
            doc=doc,
            )=="Wombat"
    assert doc[r'\wombat'].is_long == True

# XXX TODO Integration testing of edef is best done when
# XXX macro parameters are working.

def _test_expand_global_def(form_of_def, doc=None):

    if doc is None:
        doc = Document()

    result = run_code(
            r"\def\wombat{Wombat}"
            r"\wombat",
            find='chars',
            doc=doc,
            )
    assert result=="Wombat"

    doc.begin_group()

    result = run_code(
            r"\wombat"
            r"\def\wombat{Spong}"
            r"\wombat",
            find='chars',
            doc=doc,
            )
    assert result=="WombatSpong"

    doc.end_group()

    result = run_code(
            "\\wombat",
            find='chars',
            doc=doc)
    assert result=="Wombat"

    doc.begin_group()

    result = run_code(
            r"\wombat" +\
            form_of_def + r"\wombat{Spong}"
            r"\wombat",
            find='chars',
            doc=doc)
    assert result=="WombatSpong"

    doc.end_group()

    result = run_code(
            r"\wombat",
            find='chars',
            doc=doc)
    assert result=="Spong"

def test_expand_global_def():
    _test_expand_global_def(r"\global\def")

def test_expand_gdef():
    _test_expand_global_def(r"\gdef")

def test_catcode():
    # We set the catcode of ";" to 14, which makes it
    # a comment symbol.
    string = r";what\catcode`;=14 ;what"
    assert run_code(string,
            find = "chars") ==";what"

def test_chardef():
    string = r"\chardef\banana=98wom\banana at"
    assert run_code(string,
            find = "chars") =="wombat"
    string = r"\chardef\dollar=36wom\dollar at"
    assert run_code(string,
            find = "chars") =="wom$at"

def test_mathchardef():
    string = r'\mathchardef\sum="1350'
    yex.put.put(string)
    # XXX This does nothing useful yet,
    # XXX but we have the test here to make sure it parses

def run_code_the(string, doc=None, *args, **kwargs):

    if doc is None:
        doc = Document()

    seen = run_code(string,
            doc = doc,
            *args, **kwargs,
            find = 'saw',
            )

    result = ''
    for c in seen:
        if isinstance(c, yex.parse.Control):
            continue

        if isinstance(c, yex.parse.Token):
            if c.ch==32: 
                assert c.category==10 
            else: 
                assert c.category==12 

            result += c.ch

    return result

def test_the_count():
    string = r'\count20=177\the\count20'
    assert run_code_the(string) == '177'

def test_the_dimen():
    string = r'\dimen20=20pt\the\dimen20'
    assert run_code_the(string) == '20pt'

def test_let_p206_1():
    string = r'\let\a=\def \a\b{hello}\b'
    assert run_code(string,
            find = "chars") == 'hello'

def test_let_p206_2():
    string = r'\def\b{x}\def\c{y}'+\
            r'\b\c'+\
            r'\let\a=\b \let\b=\c \let\c=\a'+\
            r'\b\c'
    assert run_code(string,
            find = "chars") == 'xyyx'

def test_let_lhs_is_not_control():
    string = (
            r'\let5=5'
            )

    with pytest.raises(yex.exception.YexError):
        run_code(string,
                find='chars',
                )

def _test_font_control(
        string,
        s = None,
        ):

    if s is None:
        doc = Document()

    return doc['_font']

def test_countdef():
    string = r'\count28=17 '+\
            r'\countdef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18'+\
            r'\the\count28'
    assert run_code(string,
            find = "chars") == '1718'

def test_dimendef():
    string = r'\dimen28=17pt'+\
            r'\dimendef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18pt'+\
            r'\the\dimen28'
    assert run_code(string,
            find = "chars") == '17pt18pt'

def test_skipdef():
    string = r'\skip28=17pt plus 1pt minus 2pt'+\
            r'\skipdef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18pt plus 3pt minus 4pt'+\
            r'\the\skip28'
    assert run_code(string,
            find = "chars") == '17pt plus 1pt minus 2pt18pt plus 3pt minus 4pt'

def test_muskipdef():
    string = r'\muskip28=17pt plus 1pt minus 2pt'+\
            r'\muskipdef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18pt plus 3pt minus 4pt'+\
            r'\the\muskip28'
    assert run_code(string,
            find = "chars") == '17pt plus 1pt minus 2pt18pt plus 3pt minus 4pt'

def test_toksdef():
    string = (
            r'\toks28={Yes, we have no bananas}'
            r'\toksdef\bananas=28 '
            r'\the\bananas'
            r'\bananas={delicious and yellow}'
            r'\the\toks28'
            )
    assert run_code(string,
            find = "chars") == (
                    'Yes, we have no bananas'
                    'delicious and yellow'
                    )

# Arithmetic

def test_advance_count():
    assert run_code(
            r'\count10=100'+\
                    r'\advance\count10 by 5 '+\
                    r'\the\count10',
                    find = "chars") == '105'

def test_advance_dimen():
    assert run_code(
            r'\dimen10=10pt'+\
                    r'\advance\dimen10 by 5pt'+\
                    r'\the\dimen10',
                    find = "chars") == '15pt'

def test_multiply():
    assert run_code(
            (r'\count10=100'
                r'\multiply\count10 by 5 '
                r'\the\count10'),
            find = "chars") == '500'

def test_divide():
    assert run_code(
            (r'\count10=100'
                r'\divide\count10 by 5 '
                r'\the\count10'),
            find='chars',
            ) == '20'

# Conditionals

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

def test_conditional_ifnum_irs():
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

def test_conditional_of_modes():

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

def test_noexpand():
    assert run_code(r"\noexpand1",
            find='ch',
            )=="1"

    doc = Document()
    string = (
            r"\def\b{B}"
            r"\edef\c{1\b2\noexpand\b3\b}"
            )
    run_code(string,
            find='chars',
            doc=doc)

    assert ''.join([
        repr(x) for x in doc[r'\c'].definition
        if not x.category==x.INTERNAL
        ])==r'[1][B][2]\b[3][B]'

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
    doc = Document()

    assert _ifcat('11', doc)=='T'
    assert _ifcat('12', doc)=='T'
    assert _ifcat('AA', doc)=='T'
    assert _ifcat('AB', doc)=='T'
    assert _ifcat('1A', doc)=='F'
    assert _ifcat('A1', doc)=='F'

def test_conditional_ifcat_p209():
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

def test_conditional_ifproper():
    doc = Document()

    assert _ifproper('11', doc)=='T'
    assert _ifproper('12', doc)=='F'
    assert _ifproper('AA', doc)=='T'
    assert _ifproper('AB', doc)=='F'
    assert _ifproper('1A', doc)=='F'
    assert _ifproper('A1', doc)=='F'

def test_conditional_ifproper_p209():
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

##########################

def test_inputlineno():
    string = (
            r"\the\inputlineno"
            '\n'
            r"\the\inputlineno"
            '\n'
            '\n'
            r"\the\inputlineno"
            r"\the\inputlineno"
            )

    assert run_code(string,
            find='chars',
            )==r"1 2 44"

##########################

def test_message(capsys):
    run_code(r"\message{what}",
            find='chars')
    roe = capsys.readouterr()
    assert roe.out == "what"
    assert roe.err == ""

def test_errmessage(capsys):
    run_code(r"\errmessage{what}",
            find='chars')
    roe = capsys.readouterr()
    assert roe.out == ""
    assert roe.err == "what"

@pytest.mark.xfail
def test_special():
    found = {'x': None}
    def handle_string(self, name, s):
        found['x'] = s

    yex.control.Special.handle_string = handle_string
    run_code(r"\special{what}",
            find='chars')

    assert found['x'] == "what"

def test_register_table_name_in_message(capsys):
    # Based on ch@ck in plain.tex.
    # This doesn't parse unless the \errmessage
    # handler is run, but told not to do anything,
    # even when an if statement would ordinarily stop it.
    #
    # This is because the parser run_codes all code
    # when it's not executing. That's usually the
    # right answer, but not for \message{} and friends.

    run_code(
            r"\def\check#1#2{\ifnum\count11<#1"
            r"\else\errmessage{No room for a new #2}\fi}"
            r"\check1\dimen",
            find='chars',
            )
    roe = capsys.readouterr()
    assert roe.err == roe.out == ''

def test_expansion_with_fewer_args():
    r"""
    This is a test for currying. It's possible for a function A
    to call another function B, but supply fewer arguments than
    it needs. In that case, the remaining arguments are picked
    up from the text after the call of A.
    """
    string = (
            r"\def\friendly #1#2#3{#1 #2 my #3 friend}"
            r"\def\greet #1{#1 {Hello} {there}}"
            r"\greet\friendly {beautiful} !"
            )

    assert run_code(string,
            find='chars',
            ) == r"Hello there my beautiful friend !"

def test_expansion_with_control_at_start_of_params():
    assert run_code(
                r"\def\Look{vada}"
                r"\def\cs A\Look B#1C{wombat #1}"
                r"\cs A\Look B9C",
                find='chars',
            )==r"wombat 9"

def test_string():
    assert run_code(
            r"\string\def",
            find='chars',
            )==r"\def"

def test_def_wlog():
    assert run_code(
            # from plain.tex
            r"\def\wlog{\immediate\write\mene}",
            find='chars',
            )==''

def test_call_stack():
    STRING = (
            # 123456789012345
            r"\def\a{aXa}" "\r"        # 1
            r"" "\r"                   # 2
            r"\def\b#1{b\a b}" "\r"    # 3
            r"" "\r"                   # 4
            r"\def\c{c\b1 c}" "\r"     # 5
            r"" "\r"                   # 6
            r"\c"                      # 7
            )

    doc = Document()
    e = doc.open(STRING, on_eof='exhaust')
    for t in e:
        try:
            if t.ch=='X':
                break
        except AttributeError:
            continue

    assert e.location.line==1
    assert e.location.column==9

    found = [(x.callee, str(x.args), x.location.filename,
        x.location.line, x.location.column) for x in doc.call_stack]

    expected = [
            ('c', '{}', '<str>', 7, 3),
            ('b', '{0: [[1]]}', '<str>', 5, 11),
            ('a', '{}', '<str>', 3, 14),
            ]

    assert found==expected

    assert e.error_position("Hello")==r"""
File "<str>", line 1, in a:
  \def\a{aXa}
           ^
File "<str>", line 3, in b:
  \def\b#1{b\a b}
                ^
File "<str>", line 5, in c:
  \def\c{c\b1 c}
             ^
File "<str>", line 7, in bare code:
  \c
     ^
Error: Hello
""".lstrip()
