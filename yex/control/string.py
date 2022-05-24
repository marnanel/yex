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
import yex.exception
import sys

logger = logging.getLogger('yex.general')

class C_StringControl(C_Expandable):
    def __call__(self, tokens,
            expand=True):
        s = ''

        for t in tokens.single_shot(level='reading'):

            if t.category in (t.LETTER, t.SPACE, t.OTHER):
                s += t.ch
            else:
                s += str(t)

        if expand:
            self.handle_string(s)

class Message(C_StringControl):
    def handle_string(self, s):
        sys.stdout.write(s)

class Errmessage(C_StringControl):
    def handle_string(self, s):
        sys.stderr.write(s)
