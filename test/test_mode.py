from test import *
import yex.mode
import yex

def test_mode_switch_back():
    doc = yex.Document()

    startmode = doc['_mode']

    found = run_code(
        call = r"\hbox{X}",
        mode = None,
        doc = doc,
        on_each = lambda tokens, item: tokens.doc['_mode'],
        find = 'returns',
        )

    assert isinstance(startmode, yex.mode.Vertical)
    assert len(found)==3
    assert found[0]==found[1]
    assert startmode!=found[0]
    assert startmode is found[2] # the same instance, not just the same class
    assert isinstance(found[0], yex.mode.Restricted_Horizontal)

def test_mode_kinds_of_boxes():

    doc = yex.Document()

    startmode = doc['_mode']

    print(run_code(
        call = r"""Where is Smithy's Kaff?

Find out!""",
        mode = None,
        doc = doc,
        ))

    print(doc.output)

    assert False
