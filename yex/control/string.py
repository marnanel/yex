import logging
from yex.control.control import *
import yex.exception
import sys

macros_logger = logging.getLogger('yex.macros')
commands_logger = logging.getLogger('yex.commands')

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
