from yex.control.control import *
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
    issubclass(value, C_Control)
    ])

def handlers():
    r"""
    Returns a dict mapping control names to control handlers.

    Any class defined in this module of type `C_Control` or
    any of its subclasses will be included, with its name
    lowercased and adapted thus:

        * names beginning with `_` are not included
            (and are private to this package, so they're
            not accessible from Python code).
        * names beginning with `C_` are also not included
            (though they *are* accessible from Python code).
        * names beginning with `X_` are included, but the
            `X_` is stripped. For example, `X_Wombat`
            is included under `wombat`, and `X__Spong`
            is included under `spong`.
        * names beginning with `A_` (active characters)
            are followed by four hex digits;
            they are included under the bare character with that codepoint.
        * names beginning with `S_` (control symbols)
            are followed by four hex digits;
            they are included under the character with that codepoint
            prefixed with a backslash.
        * all other names are included, prefixed with a backslash.
            For example, `If` is included under `\if`.

    Returns:
        `dict`
    """

    def _munge(s):
        if s.startswith('X_'):
            return s[2:].lower()
        elif s.startswith('A_'):
            return chr(int(s[2:], 16))
        elif s.startswith('S_'):
            return '\\'+chr(int(s[2:], 16))
        else:
            return '\\'+s.lower()

    result = dict([
            (_munge(name), value()) for
            (name, value) in g
            if value.__class__==type and
            issubclass(value, C_Control) and
            not name.startswith('C_')
            ])

    return result
