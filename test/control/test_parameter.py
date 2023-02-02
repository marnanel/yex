from yex.document import Document
from test import *
import yex.parse

def test_parameter_getting():
    s = Document()
    s[r'\defaulthyphenchar'] = 100
    assert run_code(
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
    assert s[r'\defaulthyphenchar'] == 90

def test_parameter_output():
    doc = Document()

    assert str(doc[r'\output']) == r"\shipout\box255"
    # FIXME how can we best test this more comprehensively?

    doc[r'\output'] = [yex.parse.Other('1')]
    assert str(doc[r'\output']) == r"1"

    doc[r'\output'] = []
    assert str(doc[r'\output']) == r"\shipout\box255"

def test_parameter_prevdepth():
    doc = Document()

    assert repr(doc[r'\prevdepth'])=='-1000.0pt'

    run_code("m\r\r", doc=doc, mode=None)
    assert repr(doc[r'\prevdepth'])=='0.0pt'

    run_code("y\r\r", doc=doc, mode=None)
    assert repr(doc[r'\prevdepth'])=='1.94444pt'
