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

def test_mode_exercise_page_builder():

    doc = yex.Document()

    run_code(
            setup = r"\output={\global\box23=\box255}",
            call = r"\hbox{X}",
            doc = doc,
            )
    doc.end_all_groups()

    copy23 = doc[r'\copy23'].value
    assert len(copy23)==1
    assert len(copy23[0])==1
    assert len(copy23[0][0])==1
    assert copy23[0][0].ch=='X'
