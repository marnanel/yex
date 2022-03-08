import io
from mex.value import Tokenlist
import mex.parse
import mex.state

def _prep_string(s,
        tokens=False):
    def _category(c):
        if c==' ':
            return mex.parse.Token.SPACE
        else:
            return mex.parse.Token.OTHER

    result = [
            (c, _category(c))
            for c in s]

    if tokens:
        result = [mex.parse.Token(ch, cat)
                for (ch, cat) in result]


    return result

def _assert_tokenlist_contents(
        tl,
        expected,
        ):

    if isinstance(expected, str):
        expected = _prep_string(expected)

    assert len(tl)==len(expected)

    contents = [
            (t.ch, t.category)
            for t in tl
            ]

    assert contents==expected

def test_token_prep_string():
    assert _prep_string("Spong wombat!") == [
                ('S', 12),
                ('p', 12),
                ('o', 12),
                ('n', 12),
                ('g', 12),
                (' ', 10),
                ('w', 12),
                ('o', 12),
                ('m', 12),
                ('b', 12),
                ('a', 12),
                ('t', 12),
                ('!', 12),
                ]

def test_tokenlist_empty():
    tl = Tokenlist()

    assert bool(tl)==False

    _assert_tokenlist_contents(
            tl,
            [],
            )

def test_tokenlist_from_string():
    string = "Spong!"

    tl = Tokenlist(string)

    assert bool(tl)==True

    _assert_tokenlist_contents(
            tl,
            _prep_string(string))

def test_tokenlist_from_tokeniser():
    string = "{Wo{m b}at}let}"

    s = mex.state.State()

    with io.StringIO(string) as f:
        t = mex.parse.Tokeniser(s, f)

        tl = Tokenlist(t)

    # note: the categories are different because
    # they were assigned by the tokeniser
    _assert_tokenlist_contents(
            tl,
            [
                ('W', 11),
                ('o', 11),
                ('{', 1),
                ('m', 11),
                (' ', 10),
                ('b', 11),
                ('}', 2),
                ('a', 11),
                ('t', 11),
                ])

def test_tokenlist_equality():
    tl1 = Tokenlist('cats')
    tl2 = Tokenlist('cats')
    tl3 = Tokenlist('dogs')

    assert tl1==tl2
    assert tl1!=tl3

    assert tl1==_prep_string('cats', tokens=True)
    assert tl3!=_prep_string('cats', tokens=True)

    assert tl3=='dogs'

def test_tokenlist_subscripting():
    string = "Spong!"

    tl = Tokenlist(string)

    assert tl[2]==mex.parse.Token('o', 12)
    assert tl[-3]==mex.parse.Token('n', 12)
    assert tl[2:4]==_prep_string('on', tokens=True)

    tl[2] = mex.parse.Token('i')

    assert ''.join([x.ch for x in tl])=="Sping!"
