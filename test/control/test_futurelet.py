import yex
from test import *

def test_futurelet():
    assert run_code(
            setup = (
                r'\def\wombat{wombat}'
                r'\def\announce{We are about to write \a. Here goes.}'
                ),
            call = (
                r'\futurelet\a\announce\wombat'
                ),
            find = 'ch',
            )=='We are about to write wombat. Here goes.wombat'
