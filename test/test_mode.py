from test import *
import yex.mode
import yex

def test_mode_switch_back():
    doc = yex.Document()

    startmode = doc['_mode']

    run_code(
        call = r"\hbox{X}",
        mode = None,
        doc = doc,
        )

    endmode = doc['_mode']
    assert isinstance(startmode, yex.mode.Vertical)
    assert startmode is endmode # the same instance, not just the same class
