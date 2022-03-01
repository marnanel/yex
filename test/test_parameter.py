from mex.state import State
from . import *

def test_parameter_getting():
    s = State()
    s['defaulthyphenchar'] = 100
    assert _test_expand(r"\the\defaulthyphenchar", s)=='100'

def test_parameter_setting():
    s = State()
    s['defaulthyphenchar'] = 100
    assert _test_expand(r"\defaulthyphenchar 90", s)==''
    assert s['defaulthyphenchar'].value == 90

    s['defaulthyphenchar'] = '?'
    assert _test_expand(r"\defaulthyphenchar = 90", s)==''
    assert s['defaulthyphenchar'].value == 90
