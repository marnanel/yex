"""
Input/output controls.

These deal with access to files and streams.
"""
import logging
from yex.control.control import Unexpandable
import yex

logger = logging.getLogger('yex.general')

@yex.decorator.control()
def Input(fn: yex.filename.Filename, tokens):

    f = open(str(fn), 'r')
    inner = tokens.doc.open(f)

    class Set_Delegate(yex.parse.Internal):
        def __call__(self, tokens):
            logger.debug(
                    r"\input: setting %s's delegate to %s",
                    tokens, inner)

            if tokens.delegate is not None:
                raise yex.exception.MultipleDelegatesError()

            tokens.delegate = inner

    return Set_Delegate()

@yex.decorator.control()
def Endinput(tokens):
    tokens.exhaust_at_eol = True
