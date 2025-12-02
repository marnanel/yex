import pytest
import yex
from test import *

def test_box_parent():

    # We keep a list of (int, Box) tuples to avoid
    # having to use Box.__eq__, which isn't based
    # on identity.
    boxes = [
            (i, yex.box.HBox.from_contents(
                contents=[
                    ],
                )) for i in range(5)]
    expected = [
            (None, [])
            ] * 5

    v = yex.box.VBox()

    def index_of_box(which):
        nonlocal boxes

        return [b[0] for b in boxes
                if id(b[1])==id(which)][0]

    def get_parents():
        nonlocal boxes

        result = []
        for i, box in boxes:
            if box.parent is None:
                parent = None
            else:
                parent = index_of_box(box.parent)

            result.append(
                    (parent, [
                        index_of_box(b)
                        for b in box.contents
                        ]),
                    )

        return result

    assert get_parents()==expected

    boxes[0][1].insert(0, boxes[1][1])
    expected[0] = (None, [1])
    expected[1] = (0, [])

    assert get_parents()==expected

    boxes[0][1].insert(0, boxes[2][1])
    expected[0] = (None, [2, 1])
    expected[2] = (0, [])

    assert get_parents()==expected

    boxes[2][1].insert(0, boxes[1][1])
    expected[0] = (None, [2])
    expected[1] = (2, [])
    expected[2] = (0, [1])

    assert get_parents()==expected

    extracted = boxes[1][1].extract()
    assert extracted is boxes[1][1]
    expected[0] = (None, [2])
    expected[1] = (None, [])
    expected[2] = (0, [])

    assert get_parents()==expected
