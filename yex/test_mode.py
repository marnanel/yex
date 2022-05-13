from test import *
import yex.document

def test_word_boxes():
    doc = yex.document.Document()
    run_code("We'll travel to Venus, we'll sail away to Mars",
            doc = doc,
            )
    doc.end_all_groups() # force output

    output = doc.output[0]

    word_boxes = ';'.join([box.ch for box in output
            if isinstance(box, yex.box.WordBox)])

    assert word_boxes==(
            'We;ll;travel;to;Venus;we;ll;sail;away;to;Mars'), (
            f"list=str(output)")
