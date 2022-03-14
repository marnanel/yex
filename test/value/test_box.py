import pytest
import mex.box
from .. import *
import logging

logger = logging.getLogger('mex.general')

def test_box_simple():
    boxes = get_boxes(
            r'\hbox{a}',
            )

    assert len(boxes)==1
    assert isinstance(boxes[0], mex.box.HBox)
    assert boxes[0].contents[0].ch=='a'

def test_box_clever():
    for box_name, box_type, is_horz in [
            ('hbox', mex.box.HBox,      True),
            ('vbox', mex.box.VBox,      False),
            ('vtop', mex.box.VtopBox,   False),
            ]:

        for to_or_spread, to, spread in [
                ('', 0, 0),
                (' to 10pt', 10*65536, 0),
                (' spread 10pt', 0, 10*65536),
                ]:

            string = r'\%s%s{1}' % (
                    box_name,
                    to_or_spread,
                    )

            logger.info("Constructing box: %s",
                    string)

            found = get_boxes(string)

            assert len(found)==1
            box = found[0]

            assert isinstance(box, box_type)
            assert int(box.to)==to
            assert int(box.spread)==spread

def test_box_is_void():
    for code, expected in [
            (r'\hbox{}', True),
            (r'\hbox{a}', False),
            (r'\hbox{    }', False),
            (r'\hbox{\def\silly{}}', True),
            ]:
        saw = run_code(code,
                mode='dummy',
                find='saw',)[0]
        assert saw.is_void() == expected, f"{code} -> is_void()=={expected}"

def test_box_lastbox():
    pass

def test_box_vsplit():
    pass
