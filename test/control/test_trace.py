import pytest
import yex
from test import *

def test_trace_simple(capsys):
    yex.io.trace('octopus')
    assert capsys.readouterr().out == 'octopus\n'
