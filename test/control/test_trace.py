import pytest
import yex
import sys
from test import *

def test_trace_simple(capsys):

    # capsys has changed sys.stdout, so refresh it
    yex.io.trace.streams = [sys.stdout]

    yex.io.trace('octopus')
    assert capsys.readouterr().out == 'octopus\n'
