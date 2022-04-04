from test import *
from yex.document import Document
import yex.parse

def test_noexpand(yex_test_fs):
    assert run_code(r"\noexpand1",
            find='ch',
            )=="1"

    doc = Document()
    string = (
            r"\def\b{B}"
            r"\edef\c{1\b2\noexpand\b3\b}"
            )
    run_code(string,
            find='chars',
            doc=doc)

    assert [
        str(x) for x in doc[r'\c'].definition
        if not isinstance(x, yex.parse.Internal)
        ]==['1', 'B', '2', '\\b', '3', 'B']
