import argparse
import mex.put

def main():
    parser = argparse.ArgumentParser(
            description='typeset beautifully',
            )

    parser.add_argument('source',
                                help='source filename')
    args = parser.parse_args()

    with open(args.source, 'r') as f:
        mex.put.put(f)

if __name__=='__main__':
    main()
