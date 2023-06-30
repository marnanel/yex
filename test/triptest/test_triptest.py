"""
This file reimplements some of the tests from Knuth's trip.tex, subject to
the restrictions explained in `README.md` in this directory.

The full original trip.tex is in a multiline string at the end,
for reference.
"""

import yex
import pytest
from test import *
from triptest_text import *
import logging
import yex

logger = logging.getLogger('yex')

def start_logging(doc):
    for name in doc.controls.keys():
        if name.startswith(r'\tracing'):
            doc.controls[name] = 2

@pytest.mark.xfail
def test_triptest():
    debug_banner('Triptest begins!')

    doc = yex.Document()
    expander = doc.open(
            ORIGINAL_TRIPTEST,
            on_eof = 'exhaust',
            )

    try:
        for item in expander:
            logger.debug("-- received: %s", item)
    except:
        lines = ORIGINAL_TRIPTEST.split('\n')
        line_count = len(ORIGINAL_TRIPTEST.split('\n'))
        logger.info("Failed at line %s/%s of the source:",
                expander.location.line, len(lines))
        logger.info("%s", lines[expander.location.line])
        raise

    debug_banner('Triptest ends.')

    assert False, 'triptest is not yet fully implemented'
