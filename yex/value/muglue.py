import string
import yex.exception
import yex.parse
import logging
from yex.value.glue import Glue

commands_logger = logging.getLogger('yex.commands')

class Muglue(Glue):
    UNITS = {
            "mu": 1,
            "fi": None,
            }

    DISPLAY_UNIT = 'mu'

    UNIT_FIRST_LETTERS = set(['m', 'f'])

    def _dimen_units(self):
        return self