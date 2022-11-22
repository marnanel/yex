"""
Input/output controls.

These deal with access to files and streams.
"""
import logging
from yex.control.control import *
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
                raise yex.exception.YexInternalError(
                        "Expander already has a delegate; "
                        "this should never happen.")

            tokens.delegate = inner

    return Set_Delegate()

@yex.decorator.control()
def Endinput(tokens):
    tokens.tokeniser.source.exhaust_at_eol = True
