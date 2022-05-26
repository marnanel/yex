import yex.box
import yex.value
from yex.mode.mode import Mode
from yex.parse import *
import logging

class Math(Mode):
    is_math = True
    is_inner = True
    our_type = yex.box.HBox

    def handle(self, item, tokens):

        if isinstance(item, MathShift):
            self.doc.begin_group()
            self.doc['_mode'] = 'display_math'
            return

        super().handle(item, tokens)

    def _handle_token(self, item, tokens):
        pass

class Display_Math(Math):
    is_inner = False
