import logging
import yex
import pytest
from test import *

logger = logging.getLogger('yex.general')

def make_location():
    result = yex.parse.Location(
            filename = 'banana.tex',
            line = 23,
            column = 100,
            )
    return result

def test_location_serialise():

    something = make_location()

    assert something.filename == 'banana.tex'
    assert something.line == 23
    assert something.column == 100

    serial = something.__getstate__()

    assert serial == 'banana.tex:23:100'

    assert yex.parse.Location.from_serial(serial)==something

def test_location_read_only():

    something = make_location()

    assert something.filename == 'banana.tex'
    assert something.line == 23
    assert something.column == 100

    with pytest.raises(AttributeError):
        something.filename = 'abc.tex'

    with pytest.raises(AttributeError):
        something.line = 1

    with pytest.raises(AttributeError):
        something.column = 1
