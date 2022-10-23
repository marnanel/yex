import yex
from test import *

def test_expandafter_issue110():
    assert run_code(
            setup=(
                r'\def\spong{spong}'
                ),

            # We double up \spong to ensure that it's not working
            # merely because of pushback from the parser.
            #
            # The "le" at the end tests whether \uppercase has picked up
            # where to stop.
            call=(
                r'\uppercase{\spong\spong}le '
                r'\uppercase\expandafter{\spong\spong}le '
                ),
            find='ch',
            )=='spongspongle SPONGSPONGle'
