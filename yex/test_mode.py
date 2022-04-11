from test import *
import yex.document

def test_word_boxes():
    doc = yex.document.Document()
    run_code("We'll travel to Venus, we'll sail away to Mars",
            doc = doc,
            )
    mode = doc['_mode']

    word_boxes = ';'.join([box.ch for box in mode.list
            if isinstance(box, yex.box.WordBox)])

    assert word_boxes==(
            'We;ll;travel;to;Venus;we;ll;sail;away;to;Mars'), (
            f"list=str(mode.list)")
