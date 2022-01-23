import io
import mex.state
import mex.token

def _put_from_file(source):

    state = mex.state.State()
    result = ''

    tokens = mex.token.Tokeniser(
            state = state,
            source = source,
            )

    for item in tokens:

        if item.category in (item.LETTER, item.SPACE, item.OTHER):
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

if __name__=='__main__':
    print(put("If you see this, it works."))
