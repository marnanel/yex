import io
import pytest
from mex.state import State
from mex.token import Token, Tokeniser

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
    t = Tokeniser(s, [])
    assert t is not None

def _test_tokeniser(
        text,
        expected,
        ):
    s = State()

    result = [
            ]

    with io.StringIO(text) as f:

        t = Tokeniser(state=s, source=f)
        for item in t:
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

def test_double_caret():

    _test_tokeniser(
            text = "a^^@b",
            expected = [
                '    97 (a) Letter',
                '     0     Ignored character',
                '    98 (b) Letter',
                ],
            )

    _test_tokeniser(
            text = "a^b",
            expected = [
                '    97 (a) Letter',
                '    94 (^) Superscript',
                '    98 (b) Letter',
                ],
            )

    _test_tokeniser(
            text = "a^^6fb",
            expected = [
                '    97 (a) Letter',
                '   111 (o) Letter',
                '    98 (b) Letter',
                ],
            )

    _test_tokeniser(
            text = "a^^6=b",
            expected = [
                '    97 (a) Letter',
                '   118 (v) Letter',
                '    61 (=) Other character',
                '    98 (b) Letter',
                ],
            )

def test_active_characters():
    _test_tokeniser(
            text = "R.~J. Drofnats",
            expected = [
                '    82 (R) Letter',
                '    46 (.) Other character',
                '   126 (~) Active character',
                '    74 (J) Letter',
                '    46 (.) Other character',
                '    32 ( ) Space',
                '    68 (D) Letter',
                '   114 (r) Letter',
                '   111 (o) Letter',
                '   102 (f) Letter',
                '   110 (n) Letter',
                '    97 (a) Letter',
                '   116 (t) Letter',
                '   115 (s) Letter',
                ],
            )

def test_column():
    s = State()

    with io.StringIO("""ab
cd"""
    ) as f:
        t = Tokeniser(state=s, source=f)

        TOKENS = [
                ('a',  1, 1),
                ('b',  1, 1),
                ('\n', 2, 1),
                ('c',  2, 2),
                ('d',  2, 2),
                ]

        for ch, line, _ in TOKENS:

            token = t.__next__()
            assert token.ch == ch
            assert t.line==line

        for ch, _, line in reversed(TOKENS):

            t.push(ch)
            assert t.line==line

