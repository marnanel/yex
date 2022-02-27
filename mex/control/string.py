import logging
from mex.control.word import C_ControlWord
import mex.exception
import sys

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')

class C_StringControl(C_ControlWord):
    def __call__(self, name, tokens,
            running=True):
        s = ''
        for t in mex.parse.Expander(
                tokens=tokens,
                single=True,
                running=False):
            if t.category in (t.LETTER, t.SPACE, t.OTHER):
                s += t.ch
            else:
                s += str(t)

        if running:
            self.handle_string(name, s)

class Message(C_StringControl):
    def handle_string(self, name, s):
        sys.stdout.write(s)

class Errmessage(C_StringControl):
    def handle_string(self, name, s):
        sys.stderr.write(s)

class Special(C_StringControl):
    def handle_string(self, name, s):
        # does nothing by default
        pass


