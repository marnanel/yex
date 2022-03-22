import io
import yex.state
import yex.parse
import yex.exception
import argparse
import logging

yex_logger = logging.getLogger('yex')
macros_logger = logging.getLogger('yex.macros')
commands_logger = logging.getLogger('yex.commands')

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
        state = yex.state.State()

    result = ''

    t = yex.parse.Tokeniser(
            state = state,
            source = source,
            )
    e = yex.parse.Expander(
            t,
            on_eof=yex.parse.Expander.EOF_EXHAUST,
            )

    try:
        for item in e:
            commands_logger.debug("  -- resulting in: %s", item)

            state['_mode'].handle(
                    item=item,
                    tokens=e,
                    )

    except Exception as exception:
        if not catch:
            raise

        message = f'{exception.__class__.__name__} {exception}'
        context = t.error_position(message)

        raise PutError(
                message = message,
                context = context,
                )

    return result
