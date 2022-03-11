import io
import mex.state
import mex.parse
import mex.exception
import argparse
import logging

mex_logger = logging.getLogger('mex')
macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')

class PutError(Exception):
    def __init__(self,
            message,
            context):
        self.message = message
        self.context = context

    def __repr__(self):
        return self.context

    def __str__(self):
        return self.context

def put(source,
        state = None,
        catch = True,
        ):

    if state is None:
        state = mex.state.State()

    result = ''

    t = mex.parse.Tokeniser(
            state = state,
            source = source,
            )
    e = mex.parse.Expander(t)

    try:
        for item in e:
            commands_logger.debug("  -- resulting in: %s", item)

            try:
                item.set_from_tokens(e)
            except AttributeError:
                if item.category in (item.LETTER, item.SPACE,
                        item.OTHER, item.END_OF_LINE,
                        item.MATH_SHIFT,
                        ):

                    state.mode.handle(item)
                else:
                    raise mex.exception.MexError(
                            f"Don't know how to handle {item}")

    except Exception as exception:
        if not catch:
            raise

        message = str(exception)
        context = t.error_position(message)

        raise PutError(
                message = message,
                context = context
                )

    return result
