from mex.state import State
from . import *

def test_parameter_getting():
    s = State()
    s['defaulthyphenchar'] = 100
    assert call_macro(
            call=r"\the\defaulthyphenchar",
            state=s,
            )=='100'

def test_parameter_setting():
    s = State()
    s['defaulthyphenchar'] = 100
    assert call_macro(
            call=r"\defaulthyphenchar 90",
            state=s,
            )==''
    assert s['defaulthyphenchar'].value == 90

    s['defaulthyphenchar'] = '?'
    assert call_macro(
            call=r"\defaulthyphenchar = 90",
            state=s,
            )==''
    assert s['defaulthyphenchar'].value == 90
