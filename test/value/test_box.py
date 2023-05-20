import pytest
import yex.box
from .. import *
import logging

logger = logging.getLogger('yex.general')

def test_box_simple():
    boxes = [x for x in get_boxes(
            r'\hbox{a}',
            ) if isinstance(x, yex.box.HBox)]

    assert len(boxes)==1
    assert box_contents_to_string(boxes[0])=='^ a'

def test_box_clever():
    for box_name, box_type, is_horz in [
            ('hbox', yex.box.HBox,      True),
            ('vbox', yex.box.VBox,      False),
            ]:

        for to_or_spread, to, spread in [
                ('', 0, 0),
                (' to 10pt', 10, 0),
                (' spread 10pt', 0, 10),
                ]:

            string = r'\%s%s{\hbox{1}}' % (
                    box_name,
                    to_or_spread,
                    )

            logger.info("Constructing box: %s",
                    string)

            found = [x for x in get_boxes(string)
                    if isinstance(x, box_type)]
            assert len(found)==1, string

            box = found[0]

            assert isinstance(box, box_type), string
            assert int(box.to)==to, string
            assert int(box.spread)==spread, string

def test_box_is_void():
    for code, expected in [
            (r'\hbox{}', True),
            (r'\hbox{a}', False),
            (r'\hbox{    }', False),
            (r'\hbox{\def\silly{}}', True),
            ]:
        saw = run_code(code,
                mode='dummy',
                find='saw_all',)[0]
        assert saw.is_void() == expected, code
