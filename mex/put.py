import io
import mex.state
import mex.parse
import mex.macro
import mex.exception
import argparse
import logging

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')

def _put_from_file(source,
        state = None):

    if state is None:
        state = mex.state.State()

    result = ''

    e = mex.macro.Expander(
            mex.parse.Tokeniser(
                state = state,
                source = source,
                ))
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
                            f"Don't know category for {item}",
                            e.tokens)
    except ValueError as exception:
        raise mex.exception.MexError(str(exception), e.tokens)

    return result

def put(source,
        state = None):
    if hasattr(source, 'read'):
        return _put_from_file(source, state)
    else:
        with io.StringIO(str(source)) as f:
            return _put_from_file(f, state)
