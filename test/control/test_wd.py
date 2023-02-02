import yex
from test import *

def test_control_wd_querying():

    font = yex.font.Default()
    width_of_x = font['x'].metrics.width

    assert run_code(
            r'\box10=\hbox{x}\dimen20=\wd10(\the\dimen20)',
            find='ch',
            )==f'({width_of_x})'
