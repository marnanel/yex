from yex.control.word import *
from yex.control.table import *
from yex.control.macro import *
from yex.control.conditional import *
from yex.control.register import *
from yex.control.string import *
from yex.control.arithmetic import *
from yex.control.io import *
from yex.control.font import *
from yex.control.box import *
from yex.control.gismo import *
from yex.control.math import *
from yex.control.debug import *
from yex.control.tab import *
from yex.control.hyphen import *
from yex.control.parameter import *
from yex.control.log import *
from yex.control.other import *

# Take a copy. Sometimes evaluating a macro may
# create another macro, which changes the size
# of globals().items() and confuses the list comprehension.
g = list(globals().items())

__all__ = list([
    name for name, value in g
    if value.__class__==type and
    issubclass(value, C_ControlWord)
    ])

def handlers():

    def _munge(s):
        if s.startswith('A_'):
            # Handler for a control character, in the form A_xxxx,
            # where xxxx is a hex number
            return chr(int(s[2:], 16))
        else:
            return s.lower()

    result = dict([
            (_munge(name), value()) for
            (name, value) in g
            if value.__class__==type and
            issubclass(value, C_ControlWord) and
            not name.startswith('C_')
            ])

    return result
