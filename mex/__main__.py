import argparse
from mex.state import State
from mex.token import Token, Tokeniser, Control
from mex.macro import add_macros_to_state

def main():
    parser = argparse.ArgumentParser(
            description='transform documents',
            )

    parser.add_argument('source',
                                help='source filename')
    args = parser.parse_args()

    state = State()
    add_macros_to_state(state)

    with open(args.source, 'r') as f:
        t = Tokeniser(state = state)
        tokens = t.read(f)
        for c in tokens:

            print(c)
            if isinstance(c, Control):
                macro = c.macro()
                macro.get_params(t, tokens)
                macro()
            elif c.category==Token.END_OF_LINE:
                pass
            else:
                raise KeyError(str(c))

if __name__=='__main__':
    main()
