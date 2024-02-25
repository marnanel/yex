import yex
import pytest
from test import *

def test_controlstable_simple():
    t = yex.control.ControlsTable(wombat='banana')
    assert len(t.contents)==0
    assert len(t.macros_from_styles)==0
    assert t.kwargs['wombat'] == 'banana'

def _populated_table():
    result = yex.control.ControlsTable()
    return result

def test_controlstable_set_control():
    t = yex.control.ControlsTable()

    fred = yex.control.keyword.Iftrue()

    with pytest.raises(KeyError):
        t['fred']

    t['fred'] = fred
    assert t['fred'].name=='iftrue'

    with pytest.raises(ValueError):
        t['fred'] = 1

    t['fred'] = None

    with pytest.raises(KeyError):
        t['fred']

def test_controlstable_get():
    t = _populated_table()

def test_controlstable_keys_values_items_iter():
    t = _populated_table()
    t = yex.control.ControlsTable()

def test_controlstable_del():
    t = _populated_table()
