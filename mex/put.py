import io
import mex.state
import mex.token
import mex.macro
import argparse

def _put_from_file(source):

    state = mex.state.State()
    result = ''

    for item in mex.macro.Expander(
            mex.token.Tokeniser(
                state = state,
                source = source,
                )):
        print(item)

        if item.category in (item.LETTER, item.SPACE,
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

def main():

    parser = argparse.ArgumentParser(
            description='beautiful typesetting',
            )
    parser.add_argument('filename', type=str,
        help='file to process')

    args = parser.parse_args()
    with open(args.filename, 'r') as f:
        put(f)

if __name__=='__main__':
    main()
