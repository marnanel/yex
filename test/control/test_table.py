"""
These are tests for the controls table itself.

Therefore, don't use @yex_control_test on them.
"""
import yex
import pytest
from test import *

def test_controlstable_simple():
    t = yex.control.ControlsTable(wombat='banana')
    assert len(t.contents)==0
    assert t.kwargs['wombat'] == 'banana'

def test_controlstable_set_control():
    t = yex.control.ControlsTable()
    fred = yex.control.keyword.Iftrue()

    with pytest.raises(KeyError):
        t['fred']

    t['fred'] = fred
    assert t['fred'] == fred
    assert t.get('fred') == fred
    assert t.get('fred', param_control=False) == fred
    assert t.get('fred', param_control=True) == fred

    with pytest.raises(ValueError):
        t['fred'] = 1

    t['fred'] = None

    with pytest.raises(KeyError):
        t['fred']

def test_controlstable_set_parameter():
    t = yex.control.ControlsTable()
    jim = yex.control.keyword.Badness()

    with pytest.raises(KeyError):
        t['jim']

    t['jim'] = jim
    assert t['jim'] == 0
    assert t.get('jim') == 0
    assert t.get('jim', param_control=False) == 0
    assert t.get('jim', param_control=True) == jim

    assert isinstance(t['jim'], int)

    t['jim'] = 1
    assert t['jim'] == 1

    t['jim'] = None

    with pytest.raises(KeyError):
        t['jim']

# FIXME we must still check setitem with dict
# FIXME we must still check setitem with class

def test_controlstable_len():
    t = yex.control.ControlsTable()
    fred = yex.control.keyword.Iftrue()
    jim = yex.control.keyword.Iffalse()

    assert len(t)==0
    t['fred'] = fred
    assert len(t)==1
    t['jim'] = jim
    assert len(t)==2

def test_controlstable_keys_values_items_iter():
    t = yex.control.ControlsTable()
    fred = yex.control.keyword.Iftrue()
    jim = yex.control.keyword.Iffalse()
    sheila = yex.control.keyword.Ifcase()

    t['fred'] = fred
    t['jim'] = jim
    t['sheila'] = sheila

    assert set(t.keys())=={'fred', 'jim', 'sheila'}
    assert set(t.values())=={fred, jim, sheila}
    assert set(t.items())=={
            ('fred', fred),
            ('jim', jim),
            ('sheila', sheila),
            }

    found = set()
    for f in t:
        found.add(f)

    assert found=={'fred', 'jim', 'sheila'}

    assert 'fred' in t
    assert 'jim' in t
    assert 'sheila' in t
    assert 'margery' not in t

def test_controlstable_del():
    t = yex.control.ControlsTable()
    fred = yex.control.keyword.Iftrue()
    jim = yex.control.keyword.Iffalse()

    t['fred'] = fred
    t['jim'] = jim

    assert len(t)==2
    assert t['fred']==fred
    assert t['jim']==jim

    del t['fred']

    assert len(t)==1
    with pytest.raises(KeyError):
        t['fred']
    assert t['jim']==jim

    with pytest.raises(KeyError):
        del t['fred']

    del t['jim']

    assert len(t)==0
    with pytest.raises(KeyError):
        t['fred']
    with pytest.raises(KeyError):
        t['jim']
