from mex.control.word import *
from mex.control.table import *
from mex.control.macro import *
from mex.control.conditional import *
from mex.control.register import *
from mex.control.string import *
from mex.control.arithmetic import *
from mex.control.io import *
from mex.control.font import *
from mex.control.box import *
from mex.control.gismo import *
from mex.control.math import *
from mex.control.debug import *
from mex.control.tab import *
from mex.control.hyphen import *
from mex.control.parameter import *
from mex.control.other import *

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
        if s.startswith('X_'):
            return s[1:]
        elif s.startswith('A_'):
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
