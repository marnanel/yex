import string
import mex.exception
import mex.parse
import logging
from mex.value.glue import Glue

commands_logger = logging.getLogger('mex.commands')

class Muglue(Glue):
    UNITS = {
            "mu": 1,
            "fi": None,
            }

    DISPLAY_UNIT = 'mu'

    UNIT_FIRST_LETTERS = set(['m', 'f'])

    def _dimen_units(self):
        return self
