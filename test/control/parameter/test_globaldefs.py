from test import *
import pytest
import yex

def test_globaldefs_default_value():
    doc = yex.Document()
    assert doc.globaldefs.value == 0, "default value of globaldefs is 0"
    assert not doc.globaldefs.is_global, "is_global==False by default"

def test_globaldefs_sign():
    doc = yex.Document()

    for (v,
         expected_when_not_locked,
         expected_when_locked) in [
                 ( 0, False, True),
                 (-1, False, False),
                 (-2, False, False),
                 ( 1, True,  True),
                 ( 2, True,  True),
                 ]:

             doc.globaldefs.value = v
             assert doc.globaldefs.value == v

             assert doc.globaldefs.is_global == expected_when_not_locked, (
                     f"{v}"
                     )
             doc.globaldefs.lock_global()
             assert doc.globaldefs.is_global == expected_when_locked, (
                     f"{v}"
                     )
             doc.globaldefs.unlock_global()
             assert doc.globaldefs.is_global == expected_when_not_locked, (
                     f"{v}"
                     )

def test_globaldefs_multiple_locks():
    doc = yex.Document()

    assert doc.globaldefs.value==0
    assert doc.globaldefs.is_global==False

    for i in range(5):
        doc.globaldefs.lock_global()
        assert doc.globaldefs.is_global==True, f"{i}"

    for i in range(5):
        assert doc.globaldefs.is_global==True, f"{i}"
        doc.globaldefs.unlock_global()

    assert doc.globaldefs.is_global==False
