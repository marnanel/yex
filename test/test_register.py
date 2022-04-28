from yex.value import Tokenlist
import yex.parse
import yex.document
from test import *

def test_register_tokenlist():
    doc = yex.document.Document()

    assert doc[r'\toks23']==''

    assert run_code(
            r"\toks23={Hello}",
            doc=doc,
            find = 'chars',
            )==''

    assert doc[r'\toks23']=='Hello'

    assert run_code(
            call = r"\the\toks23",
            doc = doc,
            find = 'chars',
            )=='Hello'

def _test_textfont_etc(yex_test_fs, which):
    doc = yex.document.Document()

    assert run_code(
            setup = (
                fr'\font\thing=cmr10'
                ),
            mode='dummy',
            call = (
                fr'\{which}0=\thing'
                ),
            doc=doc,
            find='tokens',
            )==''

    assert doc[fr'\{which}0'].value.name=="cmr10", which

def test_textfont(yex_test_fs):
    _test_textfont_etc(yex_test_fs, 'textfont')

def test_scriptfont(yex_test_fs):
    _test_textfont_etc(yex_test_fs, 'scriptfont')

def test_scriptscriptfont(yex_test_fs):
    _test_textfont_etc(yex_test_fs, 'scriptscriptfont')

def test_register_none():
    doc = yex.document.Document()

    for register_name, not_none_value, none_value in [
            (r'\count23', 123, 0),
            (r'\dimen23', yex.value.Dimen(2, 'pt'), yex.value.Dimen(0)),
            (r'\skip23', yex.value.Glue(2, 'pt'), yex.value.Glue(0)),
            # TODO \toks23 etc
            ]:
        doc[register_name]=not_none_value
        assert doc[register_name].value==not_none_value, register_name
        doc[register_name]=None
        assert doc[register_name].value==none_value, register_name
