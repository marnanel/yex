from mex.state import State
from . import *

def test_parameter_getting():
    s = State()
    s['defaulthyphenchar'] = 100
    assert run_code(
            mode='vertical',
            call=r"\the\defaulthyphenchar",
            state=s,
            find='chars',
            )=='100'

def test_parameter_setting():
    s = State()
    s['defaulthyphenchar'] = 100
    assert run_code(
            call=r"\defaulthyphenchar 90",
            state=s,
            find='chars',
            )==''
    assert s['defaulthyphenchar'].value == 90

    s['defaulthyphenchar'] = '?'
    assert run_code(
            call=r"\defaulthyphenchar = 90",
            state=s,
            find='chars',
            )==''
    assert s['defaulthyphenchar'].value == 90
