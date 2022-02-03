import io
import mex.state
import mex.token
import mex.macro
import argparse
import logging

macro_logger = logging.getLogger('mex.macros')

def _put_from_file(source,
        state = None):

    if state is None:
        state = mex.state.State()

    result = ''

    e = mex.macro.Expander(
            mex.token.Tokeniser(
                state = state,
                source = source,
                ))
    for item in e:
        macro_logger.debug("  -- resulting in: %s", str(item))
        if isinstance(item, mex.state.Variable):
            item.set_from_tokens(e)
        elif item.category in (item.LETTER, item.SPACE,
                item.OTHER, item.END_OF_LINE):
            result += item.ch
        else:
            raise ValueError(f"Don't know category for {item}")

    print(result)
    return result

def put(source,
        state = None):
    if hasattr(source, 'read'):
        return _put_from_file(source, state)
    else:
        with io.StringIO(str(source)) as f:
            return _put_from_file(f, state)
