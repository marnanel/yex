import io
import mex.state
import mex.token
import mex.macro
import argparse

def _put_from_file(source):

    state = mex.state.State()
    result = ''

    e = mex.macro.Expander(
            mex.token.Tokeniser(
                state = state,
                source = source,
                ))
    for item in e:
        if isinstance(item, mex.macro.Variable):
            item.assign_from_tokens(e)
        elif item.category in (item.LETTER, item.SPACE,
                item.OTHER, item.END_OF_LINE):
            result += item.ch
        else:
            raise ValueError(f"Don't know category for {item}")

    return result

def put(source):
    if hasattr(source, 'read'):
        return _put_from_file(source)
    else:
        with io.StringIO(str(source)) as f:
            return _put_from_file(f)
