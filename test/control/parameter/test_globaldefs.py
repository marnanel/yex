from test import *
import pytest
import yex

@yex_control_test([r'\globaldefs'])
def test_globaldefs_default_value():
    doc = yex.Document()
    assert doc[r'\globaldefs'] == 0, "default value of globaldefs is 0"
    assert not doc.get_control(r'\globaldefs').is_global, "is_global==False by default"

@yex_control_test([r'\globaldefs'])
def test_globaldefs_sign():
    doc = yex.Document()

    for (v, expected_when_not_locked) in [
                 ( 0, False),
                 (-1, False),
                 (-2, False),
                 ( 1, True),
                 ( 2, True),
                 ]:

             doc[r'\globaldefs'] = v
             assert doc[r'\globaldefs'] == v

             assert doc.get_control(
                     r'\globaldefs').is_global == expected_when_not_locked, (
                     f"{v}"
                     )
             doc.get_control(r'\globaldefs').lock_global()
             assert doc.get_control(
                     r'\globaldefs').is_global == True, (
                     f"{v}"
                     )
             doc.get_control(r'\globaldefs').unlock_global()
             assert doc.get_control(
                     r'\globaldefs').is_global == expected_when_not_locked, (
                     f"{v}"
                     )

@yex_control_test([r'\globaldefs'])
def test_globaldefs_multiple_locks():
    doc = yex.Document()

    assert doc[r'\globaldefs']==0
    assert doc.get_control(r'\globaldefs').is_global==False

    for i in range(5):
        doc.get_control(r'\globaldefs').lock_global()
        assert doc.get_control(r'\globaldefs').is_global==True, f"{i}"

    for i in range(5):
        assert doc.get_control(r'\globaldefs').is_global==True, f"{i}"
        doc.get_control(r'\globaldefs').unlock_global()

    assert doc.get_control(r'\globaldefs').is_global==False
