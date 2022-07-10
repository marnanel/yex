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

class Special(C_StringControl):
    r"""
    An instruction to the output driver.

    This creates a yex.box.Whatsit which stores the instruction until
    it's shipped out. Bear in mind that it may never be shipped out.

    The argument is expanded when it's read. It consists of a keyword,
    followed optionally by a space and arguments to the keyword.
    The keyword isn't examined until the instruction is run.

    For the syntax of \special, see p276 of the TeXbook. For the syntax
    of its argument, see p225.
    """

    expander_level = 'expanding'

    def __init__(self):
        super().__init__()
        self.command = ''

    def handle_string(self, tokens, s):
        def return_special():
            return s

        result = yex.box.Whatsit(
                on_box_render = return_special,
                )

        logger.debug("special: created %s from: %s",
                result, s)

        tokens.push(result)
