from yex.value import Tokenlist
import yex.parse
import yex.document
from . import *

def test_register_tokenlist():
    doc = yex.document.Document()

    assert doc['toks23']==''

    assert run_code(
            r"\toks23={Hello}",
            doc=doc,
            find = 'chars',
            )==''

    assert doc['toks23']=='Hello'

    assert run_code(
            call = r"\the\toks23",
            doc = doc,
            find = 'chars',
            )=='Hello'
