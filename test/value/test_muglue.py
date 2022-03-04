import io
import pytest
from mex.state import State
from mex.parse import Token, Tokeniser, Expander
from mex.value import Number, Dimen, Glue
import mex.exception
from .. import *
import mex.put
import mex.box
import logging

general_logger = logging.getLogger('mex.general')

def test_muglue_literal():
    assert _get_muglue("2muq") == (2.0, 0.0, 0.0, 0, 0)
    assert _get_muglue("2mu plus 5muq") == (2.0, 5.0, 0.0, 0, 0)
    assert _get_muglue("2mu minus 5muq") == (2.0, 0.0, 5.0, 0, 0)
    assert _get_muglue("2mu plus 5mu minus 5muq") == (2.0, 5.0, 5.0, 0, 0)

def test_muglue_literal_fil():
    assert _get_muglue("2mu plus 5fil minus 5fillq") == (2.0, 5.0, 5.0, 1, 2)
    assert _get_muglue("2mu plus 5filll minus 5fillq") == (2.0, 5.0, 5.0, 3, 2)

def test_muglue_repr():
    def _test_repr(s):
        assert str(_get_muglue(f'{s}q', raw=True)) == s

    _test_repr('2mu plus 5mu')
    _test_repr('2mu plus 5fil')
    _test_repr('2mu plus 5fill')
    _test_repr('2mu plus 5filll minus 5fil')

def test_muglue_eq():
    a = _get_muglue('42mu plus 2mu minus 1muq', raw=True)
    b = _get_muglue('42mu plus 2mu minus 1muq', raw=True)
    c = _get_muglue('42mu plus 2muq', raw=True)

    for x in [a, b, c]:
        assert isinstance(x, mex.value.Muglue)

    assert a==b
    assert a!=c
    assert b!=c
