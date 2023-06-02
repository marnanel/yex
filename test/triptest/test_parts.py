# Move these somewhere more appropriate when we know where they should go.

import yex
from test import *

def test_triptest_line82():
    found = run_code(
            call = (
                r"\if00-0.\fi\ifnum'\ifnum10=10" r' 12="\fi' '\n'
                r"A 01p\ifdim1,0pt<`^^Abpt\fi\fi"
                ),
            find = 'ch',
            )

    assert found=='-0.01pt'
