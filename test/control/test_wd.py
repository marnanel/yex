import yex
from test import *

def test_control_wd_querying():
    assert run_code(
            r'\box10=\hbox{x}\dimen20=\wd10(\the\dimen20)',
            )=='(10pt)'
