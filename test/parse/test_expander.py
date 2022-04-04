import pytest
from test import *
import yex.parse
from yex.document import Document

def test_expand_simple(yex_test_fs):
    string = "This is a test"
    assert run_code(string,
            find = 'chars',
            ) == string

def test_expand_simple_def(yex_test_fs):
    assert run_code(
            setup = r'\def\wombat{Wombat}',
            call = r'\wombat',
            find = "chars",
            ) =="Wombat"

def test_expand_simple_with_nested_braces(yex_test_fs):
    string = "\\def\\wombat{Wom{b}at}\\wombat"
    assert run_code(
            string,
            find = "chars",
            ) =="Wom{b}at"

def test_expand_active_character(yex_test_fs):
    assert run_code(
            r"\catcode`X=13\def X{your}This is X life",
            find = "chars",
            ) =="This is your life"

def test_expand_with_single(yex_test_fs):
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

def test_expand_with_level_and_single(yex_test_fs):
    assert run_code(r"{\def\wombat{x}\wombat} a test",
            single=True, level='expanding',
            find = "ch") ==r"x"
    assert run_code(r"{\def\wombat{x}\wombat} a test",
            single=True, level='reading',
            find = "ch") ==r"\def\wombatx"

def test_expand_with_run_code(yex_test_fs):

    assert run_code(r"abc",
            find = "ch") == 'abc'

    assert run_code(r"\def\wombat{x}\wombat",
            find = "ch") == 'x'

    assert run_code(r"\def\wombat{x}\wombat\wombat\wombat",
            find = 'ch') == 'xxx'

def test_expand_ex_20_2(yex_test_fs):
    string = r"\def\a{\b}" +\
            r"\def\b{A\def\a{B\def\a{C\def\a{\b}}}}" +\
            r"\def\puzzle{\a\a\a\a\a}" +\
            r"\puzzle"
    assert run_code(string,
            find = "chars") =="ABCAB"

def test_expand_params_p200(yex_test_fs):
    # I've replaced \\ldots with ... because it's not
    # pre-defined here, and _ with - because it's run
    # in vertical mode.
    string = r"\def\row#1{(#1-1,...,#1-n)}\row x"
    assert run_code(string,
            find = "chars") ==r"(x-1,...,x-n)"

def test_expand_params_p201(yex_test_fs):
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

def test_expand_params_p325(yex_test_fs):
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

def test_expand_params_basic_shortargument(yex_test_fs):
    string = "\\def\\hello#1{a#1b}\\hello 1"
    assert run_code(string,
            find = "chars") =="a1b"

def test_expand_params_basic_longargument(yex_test_fs):
    string = "\\def\\hello#1{a#1b}\\hello {world}"
    assert run_code(string,
            find = "chars") =="aworldb"

def test_expand_params_with_delimiters(yex_test_fs):
    string = (
            r"\def\cs#1wombat#2spong{#2#1}"
            r"\cs wombawombatsposponspong"
            )
    assert run_code(string,
            find = "chars") =="sposponwomba"

def test_expand_params_with_prefix(yex_test_fs):
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

def test_newline_during_outer_single(yex_test_fs):
    # See the commit message for an explanation
    run_code(
        r"\outer\def\a#1{b}"
        r"\a\q %Hello world"
        "\r"
        "\r",
        find = 'ch',
        )

def test_expander_level(yex_test_fs):

    STRING = (
            r"A \iffalse B\fi C \count20 6 {D} \hbox{E}"
            )

    EXPECTED = [
            ('deep', [
                'A', ' ', r'\iffalse', 'B', r'\fi', 'C', ' ',
                r'\count', '2', '0', ' ', '6', ' ',
                '{', 'D', '}', ' ',
                r'\hbox', '{', 'E', '}',
                ' ']),

            ('reading', [
                'A', ' ', r'[\iffalse]', 'B', r'[\fi]', 'C', ' ',
                # \count is returned as a token because there is
                # no \count object as such (it's just a prefix)
                r'\count', '2', '0', ' ', '6', ' ',
                '{', 'D', '}', ' ',
                r'[\hbox]', '{', 'E', '}',
                ' ']),

            ('expanding', [
                'A', ' ', 'C', ' ',
                r'[\count20]', '6', ' ',
                '{', 'D', '}', ' ',
                r'[\hbox]', '{', 'E', '}',
                ' ']),

            ('executing', [
                'A', ' ', 'C', ' ',
                # \count20 has gone because it's been executed
                '{', 'D', '}', ' ',
                r'[\hbox:xxxx]',
                ' ']),

            ('querying', [
                'A', ' ', 'C', ' ',
                r'[\count20]', '6', ' ',
                '{', 'D', '}', ' ',
                r'[\hbox:xxxx]',
                ' ']),

            ]

    def sample(level):
        doc = yex.Document()
        t = yex.parse.Tokeniser(doc, STRING)
        e = yex.parse.Expander(t,
                level=level,
                on_eof="exhaust",
                )
        return e

    def _hbox_fix(n):
        # HBox objects have unpredictable str() values because they're
        # based on the id() value. So, to make comparison possible,
        # we replace the four unpredictable characters with xxxx.

        if len(n)==12 and n.startswith(r'[\hbox:') and n[-1]==']':
            return r'[\hbox:xxxx]'
        else:
            return n

    for level, expected in EXPECTED:
        e = sample(level=level)

        found = [_hbox_fix(str(t)) for t in e]

        assert found==expected, f"at level {level}"

def test_expander_invalid_level():
    doc = yex.Document()

    e = doc.open("", level="reading")

    with pytest.raises(yex.exception.YexError):
        e = doc.open("", level="dancing")

def test_expander_single_at_levels():

    for level in [
            'executing',
            'expanding',
            'reading',
            'deep',
            ]:
        doc = yex.Document()
        e = doc.open("{A{B}C}D")

        e = e.another(single=True, level=level,
                on_eof="exhaust")

        assert ' '.join([str(t) for t in e])=='A { B } C', f"at level {level}"

def test_expander_single_with_deep_pushback():
    # Regression test.

    for whether in [False, True]:
        doc = yex.Document()
        e = doc.open("{A{B}C}D")

        e = e.another(single=True, level="reading",
                on_eof="exhaust")

        result = []

        for t in e:
            result.append(str(t))

            if whether and str(t)=='A':
                brace = e.next(level="deep")
                assert str(brace)=='{'
                e.push(brace)
                # and this should not affect whether the outer single
                # is working

        assert result==['A', '{', 'B', '}', 'C'], f"pushback?=={whether}"

def test_expansion_with_fewer_args(yex_test_fs):
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

def test_expansion_with_control_at_start_of_params(yex_test_fs):
    assert run_code(
                r"\def\Look{vada}"
                r"\def\cs A\Look B#1C{wombat #1}"
                r"\cs A\Look B9C",
                find='chars',
            )==r"wombat 9"

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
            ('b', '{0: [the character 1]}', '<str>', 5, 11),
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
