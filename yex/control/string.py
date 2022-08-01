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
import yex
import sys

logger = logging.getLogger('yex.general')

class C_StringControl(C_Expandable):

    expander_level = 'reading'

    def __call__(self, tokens,
            expand=True):
        s = ''

        for t in tokens.single_shot(level=self.expander_level):

            if isinstance(t, (
                yex.parse.Letter,
                yex.parse.Space,
                yex.parse.Other,
                )):
                s += t.ch
            else:
                s += str(t)

        if expand:
            self.handle_string(
                    tokens = tokens,
                    s = s,
                    )

class Message(C_StringControl):
    def handle_string(self, tokens, s):
        sys.stdout.write(s)

class Errmessage(C_StringControl):
    def handle_string(self, tokens, s):
        sys.stderr.write(s)
