import pytest
import yex
from test import *

def test_box_parent():

    boxes = [
            yex.box.HBox.from_contents(
                contents=[
                    ],
                ) for i in range(5)]
    expected = [
            (None, [])
            ] * 5

    def get_parents():
        nonlocal boxes

        result = []
        for box in boxes:
            if box.parent is None:
                result.append(None)
            else:
                result.append(
                        boxes.index(box.parent))
        return result

    assert get_parents()==expected

    boxes[0].insert(0, boxes[1])
    expected[1] = (None, [1])
    expected[1] = (0, [])

    assert get_parents()==expected
