import yex.logging
import yex
from test import *

logger = yex.logging.getLogger('test')

def test_charbox():

    s = yex.Document()

    cb = yex.box.CharBox(
            font = s['_font'],
            ch = 'x',
            )

    assert int(cb.width) == 5
    assert int(cb.height) == 4
    assert int(cb.depth) == 0
    assert cb.ch == 'x'
    assert cb.__getstate__() == 'x'
