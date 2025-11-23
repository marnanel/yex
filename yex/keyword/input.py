"""
Input/output controls.

These deal with access to files and streams.
"""
import yex.logging
from yex.control.control import Unexpandable
import yex

logger = yex.logging.getLogger('control')

@yex.decorator.control()
def Input(fn: yex.filename.Filename, parser):

    f = open(str(fn), 'r')
    inner = parser.doc.open(f)

    class Set_Delegate(yex.parse.Internal):
        def __call__(self, parser):
            logger.debug(
                    r"\input: setting %s's delegate to %s",
                    parser, inner)

            parser.delegate = inner

    return Set_Delegate()

@yex.decorator.control()
def Endinput(parser):
    parser.exhaust_at_eol = True
