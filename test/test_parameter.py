from yex.document import Document
from . import *

def test_parameter_getting():
    s = Document()
    s['defaulthyphenchar'] = 100
    assert run_code(
            mode='vertical',
            call=r"\the\defaulthyphenchar",
            doc=s,
            find='chars',
            )=='100'

def test_parameter_setting():
    s = Document()
    s['defaulthyphenchar'] = 100
    assert run_code(
            call=r"\defaulthyphenchar 90",
            doc=s,
            find='chars',
            )==''
    assert s['defaulthyphenchar'].value == 90

    s['defaulthyphenchar'] = '?'
    assert run_code(
            call=r"\defaulthyphenchar = 90",
            doc=s,
            find='chars',
            )==''
    assert s['defaulthyphenchar'].value == 90
