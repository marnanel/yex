import logging
from yex.control.word import *
import yex.exception
import sys

macros_logger = logging.getLogger('yex.macros')
commands_logger = logging.getLogger('yex.commands')

class C_StringControl(C_Expandable):
    def __call__(self, name, tokens,
            expand=True):
        s = ''

        for t in tokens.single_shot(expand=False):

            if t.category in (t.LETTER, t.SPACE, t.OTHER):
                s += t.ch
            else:
                s += str(t)

        if expand:
            self.handle_string(name, s)

class Message(C_StringControl):
    def handle_string(self, name, s):
        sys.stdout.write(s)

class Errmessage(C_StringControl):
    def handle_string(self, name, s):
        sys.stderr.write(s)
