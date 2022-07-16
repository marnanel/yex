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
    assert s[r'\defaulthyphenchar'].value == 90

def test_parameter_output():
    doc = Document()

    assert str(doc[r'\output'].value) == r"\shipout\box255"
    # FIXME how can we best test this more comprehensively?

    doc[r'\output'].value = [yex.parse.Other('1')]
    assert str(doc[r'\output'].value) == r"1"

    doc[r'\output'].value = []
    assert str(doc[r'\output'].value) == r"\shipout\box255"

def test_parameter_prevdepth():
    doc = Document()

    assert doc[r'\prevdepth'].value==yex.value.Dimen(-1000, 'pt')

    run_code("m\r\r", doc=doc, mode=None)
    assert doc[r'\prevdepth'].value==yex.value.Dimen(0, 'pt')

    run_code("y\r\r", doc=doc, mode=None)
    assert doc[r'\prevdepth'].value==yex.value.Dimen(1.944, 'pt')
