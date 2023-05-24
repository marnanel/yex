import string
import yex.exception
import yex.parse
import logging
from yex.value.glue import Glue

logger = logging.getLogger('yex.general')

class Muglue(Glue):
    UNITS = {
            "mu": 65536,
            "fi": None,
            }

    DISPLAY_UNIT = 'mu'

    UNIT_FIRST_LETTERS = set(['m', 'f'])

    @classmethod
    def _dimen_units(cls):
        return cls
