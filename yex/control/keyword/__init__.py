from yex.control.keyword.arithmetic import *
from yex.control.keyword.array import *
from yex.control.keyword.box import *
from yex.control.keyword.conditional import *
from yex.control.keyword.debug import *
from yex.control.keyword.documentfield import *
from yex.control.keyword.font import *
from yex.control.keyword.gismo import *
from yex.control.keyword.hyphen import *
from yex.control.keyword.input import *
from yex.control.keyword.io import *
from yex.control.keyword.log import *
from yex.control.keyword.macro import *
from yex.control.keyword.math import *
from yex.control.keyword.number import *
from yex.control.keyword.other import *
from yex.control.keyword.parameter import *
from yex.control.keyword.register import *
from yex.control.keyword.string import *
from yex.control.keyword.tab import *

all_keyword_controls = dict([
    (name, value) for

    # Take a copy. Sometimes evaluating a macro may
    # create another macro, which changes the size
    # of globals().items() and confuses the list comprehension.
    (name, value) in list(globals().items())

    if value.__class__==type and
    value.__module__.startswith(__package__) and
    issubclass(value, Control)
    ])

__all__ = all_keyword_controls.keys()

def handlers():
    r"""
    Returns a dict mapping control.keyword.names to control.keyword.handlers.

    Any class defined in this module of type `Control` or
    any of its subclasses will be included, with its name
    lowercased and adapted thus:

        * names beginning with `_` are not included
            (and are private to this package, so they're
            not accessible from Python code).
        * names beginning with `X_` are included, but the
            `X_` is stripped. For example, `X_Wombat`
            is included under `wombat`, and `X__Spong`
            is included under `spong`.
        * names beginning with `A_` (active characters)
            are followed by four hex digits;
            they are included under the bare character with that codepoint.
        * names beginning with `S_` (control.keyword.symbols)
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
            (_munge(name), value) for
            (name, value) in all_keyword_controls.items()])

    return result
