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

def test_tokeniser_simple_text():
    s = State()
    t = Tokeniser(s)

    result = [
            ]

    with io.StringIO("""
    fred
    """) as f:

        for item in t.read(f):
            print(9, item)
            result.append(item)

    print(result)
    assert False
