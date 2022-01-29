import argparse
import mex.put
import mex.state

def main():
    parser = argparse.ArgumentParser(
            description='typeset beautifully',
            )

    parser.add_argument('source',
            help='source filename')
    parser.add_argument('--verbose', '-v',
            action="count", default=0,
            help='turn on all tracing')
    parser.add_argument('--logfile', '-L',
            default=None,
            help='log filename (implies -v); default "mex.log"')
    args = parser.parse_args()

    s = mex.state.State()
    if args.logfile:
        if args.verbose==0:
            args.verbose = 1
        s.controls['tracingonline'].logging_filename = args.logfile
        s.controls['tracingonline'].value = 0
    else:
        s.controls['tracingonline'].value = 1

    if args.verbose!=0:
        for name in s.controls.keys():
            if not name.startswith('tracing'):
                continue
            if name=='tracingonline':
                continue

            s.controls[name].value = args.verbose

    with open(args.source, 'r') as f:
        mex.put.put(f)

if __name__=='__main__':
    main()
