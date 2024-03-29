from yex.value import Tokenlist
import yex.parse
import yex.document
from test import *

def test_register_tokenlist():
    doc = yex.document.Document()

    assert str(doc[r'\toks23'])==''

    assert run_code(
            r"\toks23={Hello}",
            doc=doc,
            find = 'chars',
            )==''

    assert str(doc[r'\toks23'])=='Hello'

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

    assert doc[fr'\{which}0'].name=="cmr10", which

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
        assert doc[register_name]==not_none_value, register_name
        doc[register_name]=None
        assert doc[register_name]==none_value, register_name

def test_register_table_items():

    doc = yex.Document()

    doc[r'\count5'] = 6
    doc[r'\count23'] = 24

    found = []
    for item in doc.controls[r'\count'].items():
        found.append(item)

    assert found==[(r'\count5', 6), (r'\count23', 24)]

    found = []
    for item in doc.controls[r'\count'].keys():
        found.append(item)

    assert found==[r'\count5', r'\count23']

    found = []
    for item in doc.controls[r'\count'].values():
        found.append(item)

    assert found==[6, 24]

    assert 6 in doc.controls[r'\count']
    assert 24 in doc.controls[r'\count']
    assert 23 not in doc.controls[r'\count']

    doc[r'\uccode97'] = 90

    found = []
    for item in doc.controls[r'\uccode'].items():
        found.append(item)

    assert found==[(r'\uccode97', 90)]
