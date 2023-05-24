from test import *
import yex.parse
from yex.document import Document

def run_code_the(string, doc=None, *args, **kwargs):

    if doc is None:
        doc = Document()

    seen = run_code(string,
            doc = doc,
            *args, **kwargs,
            find = 'saw',
            )

    result = ''
    for c in seen:
        if isinstance(c, yex.parse.Control):
            continue

        if c.ch==32:
            assert isinstance(c, yex.parse.Space)
        else:
            assert isinstance(c, yex.parse.Other)

        result += c.ch

    return result

def test_the_count():
    string = r'\count20=177\the\count20'
    assert run_code_the(string) == '177'

def test_the_dimen():
    string = r'\dimen20=20pt\the\dimen20'
    assert run_code_the(string) == '20.0pt'
