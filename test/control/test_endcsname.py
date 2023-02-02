import yex
from test import *
import pytest

def test_endcsname():
    with pytest.raises(yex.exception.YexError):
        run_code(call = r'\endcsname')
