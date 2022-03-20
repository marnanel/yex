import pytest
import mex.state
from . import *

def test_io_streams_exist():
    s = mex.state.State()
    assert s['f_input;-1'] is not None
    assert s['f_input;0'] is not None
    assert s['f_input;1'] is not None
    assert s['f_input;15'] is not None
    assert s['f_input;16'] is not None

    assert s['f_output;-1'] is not None
    assert s['f_output;0'] is not None
    assert s['f_output;1'] is not None
    assert s['f_output;15'] is not None
    assert s['f_output;16'] is not None

def test_io_write_to_terminal(capsys):

    s = mex.state.State()
    string = 'Hello world\rHurrah'

    terminal = s['f_output;16']
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
