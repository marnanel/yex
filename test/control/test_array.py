from test import *
import yex

def test_register_array_name_in_params():
    found = run_code(
            setup=r'\count10=177',
            call=(
                r'\def\tenth#1{\the#110}'
                r'\tenth\count'
                ),
            find='ch',
            )
    assert found=='177'
