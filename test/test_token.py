import io
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
            as_pair = (
                    item.ch,
                    item.category,
                    )
            result.append(as_pair)

    assert result == expected
    return result

def test_tokeniser_simple_text():

    _test_tokeniser(
            text = """
    fred
    """,
    expected = [
        ('\n', 5), (' ', 10), (' ', 10), (' ', 10), (' ', 10),
        ('f', 11), ('r', 11), ('e', 11), ('d', 11), ('\n', 5),
        (' ', 10), (' ', 10), (' ', 10), (' ', 10),
        ],
    )
