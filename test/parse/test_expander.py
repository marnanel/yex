import logging
import pytest
from test import *
import yex
from yex.document import Document

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
    # If this fails saying that X is not an active character,
    # it's probably because when we read "13" (i.e. ACTIVE),
    # which was terminated with the \def statement, the \def
    # statement was interpreted while X was still not an
    # active character.
    assert run_code(
            r"\catcode`X=13\def X{your}This is X life",
            find = "chars",
            ) =="This is your life"

def test_expand_with_bounded():

    def run(call, bounded, expected):
        assert run_code(
                call=call,
                bounded=bounded,
                mode='dummy',
                output='dummy',
                find = "chars_all") == expected, f'{call} - bounded={bounded}'

    run(r"This is a test", 'no', "This is a test")

    run(r"This is a test", 'single', 'T')

    with pytest.raises(yex.exception.NeededBalancedGroupError):
        run(r"This is a test", 'balanced', '')

    run(r"{This is} a test", 'no', "{This is} a test")

    run(r"{This is} a test", 'single', 'This is')

    run(r"{This is} a test", 'balanced', 'This is')

    run(r"{Thi{s} is} a test", 'no', "{Thi{s} is} a test")

    run(r"{Thi{s} is} a test", 'single', 'Thi{s} is')

    run(r"{Thi{s} is} a test", 'balanced', "Thi{s} is")

def test_expand_with_level_and_bounded():
    assert run_code(r"{\def\wombat{x}\wombat} a test",
            bounded='single', level='expanding',
            find = "ch") ==r"x"
    assert run_code(r"{\def\wombat{x}\wombat} a test",
            bounded='single', level='reading',
            auto_save = False,
            mode = 'dummy',
            find = "ch_all") ==r"\def\wombat{x}\wombat"

    for (level, expected) in [
            ('reading', r'\def\wombat{x}\wombat'),
            ('executing', 'x'),
            ]:
        assert run_code(r"{\def\wombat{x}\wombat} a test",
                bounded='single',
                level=level,
                auto_save = False,
                mode = 'dummy',
                find = "ch_all") == expected, level

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
            find='ch_all',
            output='dummy',
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
            find='ch_all',
            mode='dummy',
            output='dummy',
            )==r"\qboxto 3pt{x}"

def test_expand_params_out_of_order():
    with pytest.raises(yex.exception.ParamsNotInOrderError):
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

    with pytest.raises(yex.exception.ZerothParameterError):
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
        with pytest.raises(yex.exception.WeirdParamSymbolError):
            string = (
                    r"\def\wombat#"
                    f"{forbidden}"
                    r"{hello}"
                    )
            run_code(string,
                    find='chars',
                    )

def test_newline_during_outer_bounded():
    # See the commit message for an explanation
    run_code(
        r"\outer\def\a#1{b}"
        r"\a\q %Hello world"
        "\r"
        "\r",
        find = 'ch',
        )

def test_expander_level():

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
                'A', ' ', r'\iffalse', 'B', r'\fi', 'C', ' ',
                # \count is returned as a token because there is
                # no \count object as such (it's just a prefix)
                r'\count', '2', '0', ' ', '6', ' ',
                '{', 'D', '}', ' ',
                r'\hbox', '{', 'E', '}',
                ' ']),

            ('expanding', [
                'A', ' ', 'C', ' ',
                r'\count20', '6', ' ',
                '{', 'D', '}', ' ',
                r'\hbox', '{', 'E', '}',
                ' ']),

            ('executing', [
                'A', ' ', 'C', ' ',
                # \count20 has gone because it's been executed
                '{', 'D', '}', ' ',
                r'[\hbox:xxxx]',
                ' ']),

            ('querying', [
                'A', ' ', 'C', ' ',
                '0', '6', ' ',
                '{', 'D', '}', ' ',
                r'[\hbox:xxxx]',
                ' ']),

            ]

    def sample(level):
        doc = yex.Document()
        doc['_mode'] = 'horizontal'

        e = yex.parse.Expander(STRING,
                level=level,
                doc=doc,
                on_eof="exhaust",
                )
        return e

    def _hbox_fix(n):
        # HBox objects have unpredictable str() values because they're
        # based on the id() value. So, to make comparison possible,
        # we replace the unpredictable characters with xxxx.

        if n.startswith(r'[\hbox;') and n[-1]==']':
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

def test_expander_bounded_at_levels():

    for level in [
            'executing',
            'expanding',
            'reading',
            'deep',
            ]:
        doc = yex.Document()
        e = doc.open("{A{B}C}D")

        e = e.another(bounded='single', level=level,
                on_eof="exhaust")

        assert ' '.join([str(t) for t in e])=='A { B } C', f"at level {level}"

def test_expander_bounded_with_deep_pushback():
    # Regression test.

    for whether in [False, True]:
        doc = yex.Document()
        e = doc.open("{A{B}C}D")

        e = e.another(bounded='single', level="reading",
                on_eof="exhaust")

        result = []

        for t in e:
            result.append(str(t))

            if whether and str(t)=='A':
                brace = e.next(level="deep")
                assert str(brace)=='{'
                e.push(brace)
                # and this should not affect whether the outer bounded
                # is working

        assert result==['A', '{', 'B', '}', 'C'], f"pushback?=={whether}"

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
            ('a', '{}', '<str>', 3, 13),
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

def test_expander_delegate_simple():

    doc = Document()

    def using_next(e, ei):
        return next(ei)

    def using_method(e, ei):
        return e.next()

    for how in [using_next, using_method]:

        e = doc.open('ABC', on_eof='none')
        ei = iter(e)

        assert how(e, ei).ch=='A'

        e.delegate = doc.open('PQR', on_eof='exhaust')

        assert how(e, ei).ch=='P'
        assert how(e, ei).ch=='Q'
        assert how(e, ei).ch=='R'
        assert how(e, ei).ch==' ' # eol
        assert how(e, ei).ch=='B'
        assert how(e, ei).ch=='C'
        assert how(e, ei).ch==' ' # eol
        assert how(e, ei) is None

def test_expander_delegate_raise():
    doc = Document()
    e = doc.open('ABC', on_eof='none')

    assert e.next().ch=='A'

    e.delegate = doc.open('PQR', on_eof='exhaust')

    assert e.next().ch=='P'
    assert e.next().ch=='Q'
    assert e.next().ch=='R'
    assert e.next().ch==' '
    assert e.next().ch=='B'
    assert e.next().ch=='C'
    assert e.next().ch==' '

    with pytest.raises(yex.exception.UnexpectedEOFError):
        e.next(on_eof='raise')

def test_expander_with_doc_specified():
    doc1 = Document()
    doc2 = Document()
    tok2 = yex.parse.Tokeniser(doc=doc2, source='')

    exp2 = yex.parse.Expander(source=tok2)
    assert exp2.doc == doc2

    exp1 = yex.parse.Expander(source=tok2, doc=doc1)
    assert exp1.doc == doc1

    # specify level so that it's forced to create a new Expander
    exp2a = exp2.another(level='deep')
    assert exp2a.doc == doc2

    exp1a = exp2.another(level='deep', doc=doc1)
    assert exp1a.doc == doc1

def test_expander_with_source():
    doc = Document()
    e1 = yex.parse.Expander(source='apples', doc=doc, on_eof='exhaust')
    assert '/'.join([str(t) for t in e1]) == 'a/p/p/l/e/s/ '

    e2 = e1.another(source='oranges')
    assert '/'.join([str(t) for t in e2]) == 'o/r/a/n/g/e/s/ '

    with pytest.raises(ValueError):
        dummy = yex.parse.Expander(source='fred')

def test_expander_active_makes_active():
    doc = Document()

    for letter in 'PQ':
        doc.controls[r'\catcode'][ord(letter)] = yex.parse.Token.ACTIVE

    e = doc.open((
            r"\defP{Q}"
            r"\defQ{R}"
            r"APB"),
            on_eof='none',
            )

    assert e.next().ch=='A'
    assert e.next().ch=='R'
    assert e.next().ch=='B'
    assert e.next().ch==' '
    assert e.next() is None

def test_expander_eat_optional_spaces():

    def make_expander():
        doc = Document()

        doc.controls[r'\catcode'][ord('P')] = yex.parse.Token.ACTIVE

        e = doc.open(
            r"\defP{ }"
            r"A PBC")

        return e

    e = make_expander()
    assert e.next().ch=='A'
    assert [str(x) for x in e.eat_optional_spaces()] == [' ']

    assert e.next().ch==' '
    assert e.next().ch=='B', (
            'the tokeniser can only ignore actual spaces'
            )

    e = make_expander()
    assert e.next().ch=='A'
    assert [str(x) for x in e.eat_optional_spaces(
        level='deep',
        )] == [' ']
    assert e.next().ch==' '
    assert e.next().ch=='B', (
            'the expander can delegate to the tokeniser'
            )

    e = make_expander()
    assert e.next().ch=='A'
    assert [str(x) for x in e.eat_optional_spaces()] == [' ']
    assert e.next().ch==' '
    assert e.next().ch=='B', (
            'the expander defaults to delegating to the tokeniser'
            )

    e = make_expander()
    assert e.next().ch=='A'
    assert [str(x) for x in e.eat_optional_spaces(
        level='querying',
        )] == [' '] * 2
    e.eat_optional_spaces()
    assert e.next().ch=='B', (
            'the expander ignores spaces produced by execution'
            )
    e.eat_optional_spaces()
    assert e.next().ch=='C', (
            'the expander eats nothing if there are no spaces'
            )

def test_expander_pushback_full():

    def run(pushed, source, expected):

        doc = Document()

        e = yex.parse.Expander(
                source,
                doc=doc,
                on_eof='exhaust',
                )

        e.push(pushed)
        doc.end_all_groups()
        found = ''.join([item.ch for item in e]).rstrip()
        assert found==expected, f"pushed={pushed}, source={source}"

    run('b', 'ovine', 'bovine')
    run('secret', 'arial', 'secretarial')
    run(None, 'wombat', 'wombat')
    run([chr(x) for x in range(ord('n'), ord('q'))],
            'roblem',
            'noproblem')

def test_expander_pushback_partway(fs):
    doc = Document()
    e = yex.parse.Expander(
            'dogs',
            doc=doc,
            on_eof='exhaust',
            )
    i = iter(e)

    def get():
        try:
            return next(i).ch
        except StopIteration:
            return None

    assert get()=='d'
    assert get()=='o'
    e.pushback.push('i')
    assert get()=='i'
    assert get()=='g'
    e.pushback.push('t')
    e.pushback.push('a')
    e.pushback.push('c')
    assert get()=='c'
    assert get()=='a'
    assert get()=='t'
    assert get()=='s'
    assert get()==' '
    assert get() is None

def test_expander_end():
    doc = Document()

    def take_three_letters_and_then_end(e):
        assert e.next().ch=='w'
        assert e.next().ch=='o'
        assert e.next().ch=='m'
        e.end()

    e = yex.parse.Expander('wombats', doc=doc, on_eof='exhaust')
    take_three_letters_and_then_end(e)
    with pytest.raises(StopIteration):
        item = e.next()

    e = yex.parse.Expander('wombats', doc=doc, on_eof='none')
    take_three_letters_and_then_end(e)
    assert e.next() is None

    e = yex.parse.Expander('wombats', doc=doc, on_eof='raise')
    take_three_letters_and_then_end(e)
    with pytest.raises(yex.exception.UnexpectedEOFError):
        item = e.next()

def test_expander_invalid_char(caplog):

    caplog.set_level(logging.WARN, logger='yex')

    doc = Document()

    doc[r'\catcode42'] = yex.parse.token.Token.INVALID

    doc.read('*')

    assert len(caplog.record_tuples)==1
    assert caplog.record_tuples[0][2] == "Invalid character found: '*'"

def test_expander_if_in_number():
    with pytest.raises(ValueError):
        run_code(
                r'\catcode`X=13\iffalse8\fi3'
                )
