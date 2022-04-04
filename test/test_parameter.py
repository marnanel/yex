from yex.document import Document
from . import *

def test_parameter_getting(yex_test_fs):
    s = Document()
    s[r'\defaulthyphenchar'] = 100
    assert run_code(
            mode='vertical',
            call=r"\the\defaulthyphenchar",
            doc=s,
            find='chars',
            )=='100'

def test_parameter_setting():
    s = Document()
    s[r'\defaulthyphenchar'] = 100
    assert run_code(
            call=r"\defaulthyphenchar 90",
            doc=s,
            find='chars',
            )==''
    assert s[r'\defaulthyphenchar'].value == 90

    s[r'\defaulthyphenchar'] = '?'
    assert run_code(
            call=r"\defaulthyphenchar = 90",
            doc=s,
            find='chars',
            )==''
    assert s[r'\defaulthyphenchar'].value == 90
