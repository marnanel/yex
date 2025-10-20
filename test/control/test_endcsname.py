import yex
from test import *
import pytest

@yex_control_test([r'\endcsname'])
def test_endcsname():
    with pytest.raises(yex.exception.YexError):
        run_code(call = r'\endcsname')
