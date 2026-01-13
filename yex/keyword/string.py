r"""
String controls.

These are special-cased inside Parser: they are run even if we're
prevented from executing (for example, by \iffalse). This is because of the
way printed messages are evaluated by TeX. But it's rather hacky and we should
merge that with yex.control.conditional at some point.

Confusingly, \string is not a string control; it's in yex.control.other.
"""
import yex.logging
from yex.control.control import Unexpandable
from yex.decorator import control
import yex
import sys

logger = yex.logging.getLogger('control')

@control(even_if_not_expanding=True)
def _Write_Message(self, parser, reading_all_args):
    self.write_message(
            parser = parser,
            s= reading_all_args,
            )

class Message(_Write_Message):
    def write_message(self, parser, s):
        if parser.is_expanding:
            self._output(s)

    def _output(self, s):
        self.stream.write(s)

    @property
    def stream(self):
        return sys.stdout

class Errmessage(Message):
    @property
    def stream(self):
        return sys.stderr
