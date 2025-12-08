import yex
import pytest
from test import *

@yex_control_test([r'\accent'])
@pytest.mark.xfail
def test_keyword_accent():

    # the control: just write an A

    run_code('A')

    assert False
