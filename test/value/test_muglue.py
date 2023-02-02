import io
import pytest
import copy
from yex.document import Document
from yex.value import Number, Dimen, Glue, Muglue
import yex.exception
from .. import *
import yex.put
import yex.box
import logging

logger = logging.getLogger('yex.general')

def test_muglue_literal():
    assert get_muglue("2.0muq") == (2.0, 0.0, 0.0, 0, 0)
    assert get_muglue("2.0mu plus 5.0muq") == (2.0, 5.0, 0.0, 0, 0)
    assert get_muglue("2.0mu minus 5.0muq") == (2.0, 0.0, 5.0, 0, 0)
    assert get_muglue("2.0mu plus 5.0mu minus 5.0muq") == (2.0, 5.0, 5.0, 0, 0)

def test_muglue_literal_fil():
    assert get_muglue("2.0mu plus 5.0fil minus 5.0fillq") == (
            2.0, 5.0, 5.0, 1, 2)
    assert get_muglue("2.0mu plus 5.0filll minus 5.0fillq") == (
            2.0, 5.0, 5.0, 3, 2)

def test_muglue_repr():
    def _test_repr(s):
        assert str(get_muglue(f'{s}q', raw=True)) == s

    _test_repr('2.0mu plus 5.0mu')
    _test_repr('2.0mu plus 5.0fil')
    _test_repr('2.0mu plus 5.0fill')
    _test_repr('2.0mu plus 5.0filll minus 5.0fil')

def test_muglue_eq():
    a = get_muglue('42.0mu plus 2.0mu minus 1.0muq', raw=True)
    b = get_muglue('42.0mu plus 2.0mu minus 1.0muq', raw=True)
    c = get_muglue('42.0mu plus 2.0muq', raw=True)

    for x in [a, b, c]:
        assert isinstance(x, yex.value.Muglue)

    assert a==b
    assert a!=c
    assert b!=c

    assert a!=None
    assert not (a==None)

def test_muglue_deepcopy():
    # Constructed from literal
    compare_copy_and_deepcopy(Muglue(0))

    # Constructed from tokeniser
    compare_copy_and_deepcopy(get_muglue("1.0mu plus 2.0muq", raw=True))
