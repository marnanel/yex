import io
import pytest
from yex.state import State
from yex.parse import Token, Tokeniser
from .. import *

def test_token_simple_create():
    t = Token('q', 0)
    assert t is not None

def test_token_location():
    t = Token('q', 0,
            location=('foo', 1, 2))
    assert t is not None
    assert t.location==('foo', 1, 2)

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

def test_token_no_category_given():
    string = 'Hello world!'
    result = ''

    for letter in string:
        t = Token(ch=letter)
        result += str(t.ch)+str(t.category)

    assert result=="H12e12l12l12o12 10w12o12r12l12d12!12"

def test_token_deepcopy():
    compare_copy_and_deepcopy(Token('q'))

    with expander_on_string("q") as e:
        t = e.next()
        compare_copy_and_deepcopy(t)
