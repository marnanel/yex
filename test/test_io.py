import pytest
import yex.document
from . import *

def test_io_streams_exist():
    s = yex.document.Document()
    assert s['_input;-1'] is not None
    assert s['_input;0'] is not None
    assert s['_input;1'] is not None
    assert s['_input;15'] is not None
    assert s['_input;16'] is not None

    assert s['_output;-1'] is not None
    assert s['_output;0'] is not None
    assert s['_output;1'] is not None
    assert s['_output;15'] is not None
    assert s['_output;16'] is not None

def test_io_write_to_terminal(capsys):

    s = yex.document.Document()
    string = 'Hello world\rHurrah'

    terminal = s['_output;16']
    terminal.write(string)
    result = capsys.readouterr().out

    assert result==string.replace('\r', '\n')

@pytest.mark.xfail
def test_io_write_to_file():
    assert False

@pytest.mark.xfail
def test_io_write_to_log_but_not_terminal():
    assert False

@pytest.mark.xfail
def test_io_read_from_terminal():
    assert False

@pytest.mark.xfail
def test_io_read_from_file():
    assert False
