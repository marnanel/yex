r"""
String controls.

These are special-cased inside Expander: they are run even if we're
prevented from executing (for example, by \iffalse). This is because of the
way printed messages are evaluated by TeX. But it's rather hacky and we should
merge that with yex.control.conditional at some point.

Confusingly, \string is not a string control; it's in yex.control.other.
"""
import logging
from yex.control.control import *
from yex.decorator import control
import yex
import sys

logger = logging.getLogger('yex.general')

@control(even_if_not_expanding=True)
def Message(tokens, reading_all_args):
    if tokens.is_expanding:
        sys.stdout.write(reading_all_args)

@control(even_if_not_expanding=True)
def Errmessage(tokens, reading_all_args):
    if tokens.is_expanding:
        sys.stderr.write(reading_all_args)
