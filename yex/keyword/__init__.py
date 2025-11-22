from yex.keyword.arithmetic import *
from yex.keyword.array import *
from yex.keyword.box import *
from yex.keyword.conditional import *
from yex.keyword.debug import *
from yex.keyword.documentfield import *
from yex.keyword.font import *
from yex.keyword.gismo import *
from yex.keyword.hyphen import *
from yex.keyword.input import *
from yex.keyword.io import *
from yex.keyword.macro import *
from yex.keyword.math import *
from yex.keyword.number import *
from yex.keyword.other import *
from yex.keyword.parameter import *
from yex.keyword.register import *
from yex.keyword.string import *
from yex.keyword.tab import *
from yex.keyword.trace import *

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
    Returns a dict mapping keyword.names to keyword.handlers.

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
        * names beginning with `S_` (keyword.symbols)
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
