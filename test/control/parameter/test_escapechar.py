import yex
from test import *

@yex_control_test([r'\escapechar'])
def test_escapechar():
    doc = yex.Document()

    for escapechar, expected in [
            ( 42, '*if'),
            ( 64, '@if'),
            ( 65, 'Aif'),
            ( -1, 'if'),
            (256, 'if'),
            ]:
        doc[r'\escapechar'] = escapechar
        assert run_code(r'\string\if', doc=doc, find='ch')==expected, \
                escapechar
