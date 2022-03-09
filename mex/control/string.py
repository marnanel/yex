import logging
from mex.control.word import C_ControlWord
import mex.exception
import sys

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')

class C_StringControl(C_ControlWord):
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
