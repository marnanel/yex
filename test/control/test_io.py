import pytest
import yex.document
from test import *

def test_immediate_write_simple(capsys):
    assert run_code(
            r"\immediate\write-1{Hello world.}",
            find='chars',
            )==""
    result = capsys.readouterr().out
    assert result.strip()=="Hello world."

def test_immediate_write_side_effect(capsys):
    doc = yex.document.Document()

    assert doc['count1'].value==0
    assert run_code(
            r"\immediate\write-1{Hello \count1=2 world.}",
            find='chars',
            doc=doc,
            )==""
    assert doc['count1'].value==2

    result = capsys.readouterr().out
    assert result.strip()=="Hello world."
