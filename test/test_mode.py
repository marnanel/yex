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
    assert box_contents_to_string(copy23)=='[^ X]'

def test_word_boxes():
    doc = yex.Document()
    run_code("We'll travel to Venus, we'll sail away to Mars",
            doc = doc,
            )
    doc.end_all_groups() # force output

    output = doc.output[0]
    found = [x for x in doc.output[0] if isinstance(x, yex.box.Box)]

    word_boxes = ';'.join([box.ch for box in found[0]
            if isinstance(box, yex.box.WordBox)])

    assert word_boxes==(
            "We'll;travel;to;Venus,;we'll;sail;away;to;Mars"), (
            f"list=str(output)")
