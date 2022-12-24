import logging
import yex
from test import *

logger = logging.getLogger('yex.general')

def test_kern_getstate():
    g = yex.box.Kern(yex.value.Dimen(123, 'pt'))
    assert g.__getstate__()=={'kern': 123*65536}
