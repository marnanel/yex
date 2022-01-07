import argparse
from mex.state import State
from mex.token import Token, Tokeniser, Control

def main():
    parser = argparse.ArgumentParser(
            description='transform documents',
            )

    parser.add_argument('source',
                                help='source filename')
    args = parser.parse_args()

    state = State()

    with open(args.source, 'r') as f:
        t = Tokeniser(state = state)
        for c in t.read(f):

            print(c)
            if isinstance(c, Control):
                print(999, c)
            elif c.category==Token.END_OF_LINE:
                pass
            else:
                raise KeyError(str(c))

if __name__=='__main__':
    main()
