import io
import pytest
from yex.document import Document
from yex.parse import *
import yex.parse.source
from test import *
import string

def test_token_simple_create():
    t = Token.get('q', 0)
    assert t is not None

def test_token_location():
    t = Token.get('q', 0,
            location=('foo', 1, 2))
    assert t is not None
    assert t.location==('foo', 1, 2)

def test_token_cats():

    somewhere = yex.parse.Location(
            filename = 'a',
            line = 1,
            column = 1,
            )

    for category, cls, meaning in [
            ( 0, Escape,         'escape character'),
            ( 1, BeginningGroup, 'begin-group character X'),
            ( 2, EndGroup,       'end-group character X'),
            ( 3, MathShift,      'math shift character X'),
            ( 4, AlignmentTab,   'end of alignment template'),
            ( 6, Parameter,      'macro parameter character X'),
            ( 7, Superscript,    'superscript character X'),
            ( 8, Subscript,      'subscript character X'),
            (10, Space,          'blank space X'),
            (11, Letter,         'the letter X'),
            (12, Other,          'the character X'),
            (13, Active,         'the active character X'),
            ]:

        t = Token.get(ch='X', category=category, location=somewhere)
        assert t.category==category
        assert t.ch == 'X'
        assert t.location == somewhere
        assert isinstance(t, cls)
        assert t.meaning == meaning

    for unavailable in [5, 9, 14, 15]:
        with pytest.raises(ValueError):
            t = Token.get(ch='X', category=unavailable, location=somewhere)

def test_token_no_category_given():
    string = 'Hello world!'
    result = ''

    for letter in string:
        t = Token.get(ch=letter)
        result += str(t.ch)+str(t.category)

    assert result=="H12e12l12l12o12 10w12o12r12l12d12!12"

def test_token_deepcopy():
    compare_copy_and_deepcopy(Token.get('q'))

    with expander_on_string("q") as e:
        t = e.next()
        compare_copy_and_deepcopy(t)

def test_token_serialise_list():

    def _find_category(c):
        if c in string.ascii_letters:
            return Token.LETTER
        elif c in string.whitespace:
            return Token.SPACE
        else:
            return Token.OTHER

    def run(original, expected, strip_singleton=False):
        found = Token.serialise_list(original, strip_singleton)
        assert found==expected

        round_trip = Token.deserialise_list(found)

        assert original == round_trip

    things = [
            Token.get(
                category=_find_category(c),
                ch=c,
                ) for c in "Hello world 123"]

    run(things, ['Hello world 123'])
    run(things, 'Hello world 123', strip_singleton=True)

    things = [
            Token.get(
                category=_find_category(c),
                ch=c,
                ) for c in "Hello world 123"]

    things[2] = Token.get(ch='#', category=Token.PARAMETER)
    run(things, ['He##lo world 123'])

    things[2] = Token.get(ch='#', category=Token.OTHER)
    run(things, ['He', [Token.OTHER, '#'], 'lo world 123'])

def test_token_deserialise_arguments():

    for max_arg in range(1, 10):
        for arg in range(1, 10):

            try:
                found = Token.deserialise_list(f'#{arg}',
                        max_arg = max_arg,
                        )

                assert arg <= max_arg
                assert len(found)==1
                assert isinstance(found[0], Argument)
                assert found[0].index==arg

            except ValueError:
                assert arg > max_arg

    with pytest.raises(ValueError):
        Token.deserialise_list("#x")

def test_token_is_from_tex():
    assert Escape.is_from_tex()
    assert BeginningGroup.is_from_tex()
    assert EndGroup.is_from_tex()
    assert MathShift.is_from_tex()
    assert AlignmentTab.is_from_tex()
    assert Parameter.is_from_tex()
    assert Superscript.is_from_tex()
    assert Subscript.is_from_tex()
    assert Space.is_from_tex()
    assert Letter.is_from_tex()
    assert Other.is_from_tex()
    assert Active.is_from_tex()
    assert not ControlName.is_from_tex()
    assert not Internal.is_from_tex()
    assert not Paragraph.is_from_tex()

def test_token_is_implicit():
    saw = run_code(
            setup=r"\let\bgroup={\let\egroup=}",
            call=r"\bgroup\egroup{}",
            find='saw_all',
            no_repeats = True,
            )

    found = [(t.ch, t.category, t.implicit) for t in saw]

    assert found == [
            ('{', 1, True),
            ('}', 2, True),
            ('{', 1, False),
            ('}', 2, False),
            ]

    saw = run_code(
            setup=r"\def\aa{aa}",
            call=r"a\aa a",
            find='saw_all',
            no_repeats = True,
            )

    found = [(t.ch, t.category, t.implicit) for t in saw]

    assert found == [
            ('a', 11, False),
            ('a', 11, True),
            ('a', 11, True),
            ('a', 11, False),
            ]

def test_token_is_a_type_error():

    for (cat, it_isnt) in [
            (Letter, 1234),
            (Letter, None),
            (Letter, 'cheese'),
            (Other,  1234),
            (Other,  None),
            (Other,  'cheese'),
            ]:
        with pytest.raises(TypeError):
            cat().is_a(it_isnt)

def test_token_is_a_basic():
    tokens = [
            Letter(ch='1'),
            Other(ch='2'),
            Superscript(ch='3'),
            ]

    for c, expected in [
            (Other, 'FTF'),
            ( (Other,), 'FTF'),
            ( (Other, Letter), 'TTF'),
            ( (Letter, Other), 'TTF'),
            ( Superscript, 'FFT')
            ]:
        found = ''.join([str(
                t.is_a(c)
                )[0] for t in tokens])

        assert found==expected, c


def test_token_is_a_complicated():
    for       implicit, allow,      cat, comparand, expected in [

            (    False, False, Letter,  Letter,   True,  ),
            (    False, False, Letter,  Other,    False, ),
            (    False, False, Other,   Letter,   False, ),
            (    False, False, Other,   Other,    True,  ),

            (    False, True,  Letter,  Letter,   True,  ),
            (    False, True,  Other,   Letter,   False, ),
            (    False, True,  Other,   Letter,   False, ),
            (    False, True,  Other,   Other,    True,  ),

            (    True,  False, Letter,  Letter,   False, ),
            (    True,  False, Other,   Letter,   False, ),
            (    True,  False, Other,   Letter,   False, ),
            (    True,  False, Other,   Other,    False, ),

            (    True,  True,  Letter,  Letter,   True,  ),
            (    True,  True,  Other,   Letter,   False, ),
            (    True,  True,  Other,   Letter,   False, ),
            (    True,  True,  Other,   Other,    True,  ),

            ]:

        details = (implicit, allow, cat, comparand, expected)
        left = cat(ch='m')

        if implicit:
            left.implicit = True

        if not allow:
            assert left.is_a(comparand)==expected, details

        assert left.is_a(comparand, allow_implicit=allow)==expected, details

def test_token_paired_implicits():
    run_code(setup=r"""
\let\ca={ \let\ce=}
\def\ba{\ca}
\def\be{\ce}""",
             call=r"""
\count10=1 \the\count10 {\the\count10 \count10=2 \the\count10 }\the\count10 \count10=3 \the\count10

\count10=1 \the\count10 \ba\the\count10 \count10=2 \the\count10 }\the\count10 \count10=3 \the\count10

\count10=1 \the\count10 {\the\count10 \count10=2 \the\count10 \be\the\count10 \count10=3 \the\count10

\count10=1 \the\count10 \ca\the\count10 \count10=2 \the\count10 }\the\count10 \count10=3 \the\count10

\count10=1 \the\count10 {\the\count10 \count10=2 \the\count10 \ce\the\count10 \count10=3 \the\count10
             """)
