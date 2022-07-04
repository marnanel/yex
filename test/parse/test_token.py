import io
import pytest
from yex.document import Document
from yex.parse import *
import yex.parse.source
from test import *
import string

def test_token_simple_create():
    t = get_token('q', 0)
    assert t is not None

def test_token_location():
    t = get_token('q', 0,
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

        t = get_token(ch='X', category=category, location=somewhere)
        assert t.category==category
        assert t.ch == 'X'
        assert t.location == somewhere
        assert isinstance(t, cls)
        assert t.meaning == meaning

    for unavailable in [5, 9, 14, 15]:
        with pytest.raises(ValueError):
            t = get_token(ch='X', category=unavailable, location=somewhere)

def test_token_no_category_given():
    string = 'Hello world!'
    result = ''

    for letter in string:
        t = get_token(ch=letter)
        result += str(t.ch)+str(t.category)

    assert result=="H12e12l12l12o12 10w12o12r12l12d12!12"

def test_token_deepcopy():
    compare_copy_and_deepcopy(get_token('q'))

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
            get_token(
                category=_find_category(c),
                ch=c,
                ) for c in "Hello world 123"]

    run(things, ['Hello world 123'])
    run(things, 'Hello world 123', strip_singleton=True)

    things = [
            get_token(
                category=_find_category(c),
                ch=c,
                ) for c in "Hello world 123"]

    things[2] = get_token(ch='#', category=Token.PARAMETER)
    run(things, ['He#lo world 123'])

    things[2] = get_token(ch='#', category=Token.OTHER)
    run(things, ['He', [Token.OTHER, '#'], 'lo world 123'])
