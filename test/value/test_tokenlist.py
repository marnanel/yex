import io
import string
import pytest
from yex.value import Tokenlist
from .. import *
import yex.parse
import yex.document

def _prep_string(s,
        as_if_plain = True,
        tokens=False,
        ):
    def _category(c):
        if as_if_plain:
            if c in string.ascii_letters:
                return yex.parse.Token.LETTER

        if c==' ':
            return yex.parse.Token.SPACE
        else:
            return yex.parse.Token.OTHER

    result = [
            (c, _category(c))
            for c in s]

    if tokens:
        result = [yex.parse.Token.get(ch, cat)
                for (ch, cat) in result]

    return result

def _assert_tokenlist_contents(
        tl,
        expected,
        ):

    if isinstance(expected, str):
        expected = _prep_string(expected)

    try:
        assert len(tl)==len(expected)
    except TypeError:
        # Expanders don't have a len()
        pass

    found = []

    for t in tl:
        if t is None:
            break
        elif isinstance(t, yex.parse.Token):
            found.append(
                (t.ch, t.category)
                )
        else:
            found.append(t)

    assert found==expected

def test_token_prep_string():
    assert _prep_string("Spong wombat!") == [
                ('S', 11),
                ('p', 11),
                ('o', 11),
                ('n', 11),
                ('g', 11),
                (' ', 10),
                ('w', 11),
                ('o', 11),
                ('m', 11),
                ('b', 11),
                ('a', 11),
                ('t', 11),
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

def test_tokenlist_from_expander():
    string = "{Wo{m b}at}let}"

    tl = yex.document.Document().open(string,
            bounded='single',
            on_eof='exhaust',
            )

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

def test_tokenlist_from_list():

    string = "Wombat spong!"
    v = [
            yex.parse.Token.get(c)
            for c in string
            ]

    tl = Tokenlist(v)

    _assert_tokenlist_contents(
            tl,
            _prep_string(string,
                as_if_plain=False,
                ))

    with pytest.raises(TypeError):
        v.append(1)
        tl = Tokenlist(v)

def test_tokenlist_equality():
    tl1 = Tokenlist('cats')
    tl2 = Tokenlist('cats')
    tl3 = Tokenlist('dogs')

    assert tl1==tl2
    assert tl1!=tl3

    assert tl1==_prep_string('cats', tokens=True)
    assert tl3!=_prep_string('cats', tokens=True)

def test_tokenlist_subscripting():
    string = "Spong!"

    tl = Tokenlist(string)

    assert tl[2]==yex.parse.Token.get('o', 11)
    assert tl[-3]==yex.parse.Token.get('n', 11)
    assert tl[2:4]==_prep_string('on', tokens=True)

    tl[2] = yex.parse.Token.get('i')

    assert ''.join([x.ch for x in tl])=="Sping!"

def test_tokenlist_deepcopy():
    # Constructed from literal
    compare_copy_and_deepcopy(Tokenlist("wombat"))

    # Constructed from tokeniser
    tokens = yex.document.Document().open("{wombat}")
    compare_copy_and_deepcopy(Tokenlist(tokens))
