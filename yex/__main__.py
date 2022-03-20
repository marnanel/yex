import argparse
import sys
import yex.put
import yex.state
import traceback

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
            help='log filename (implies -v); default "yex.log"')
    parser.add_argument('--fonts-dir', '-f',
            default='other',
            help='directory with fonts in')
    parser.add_argument('--python-traceback', '-P',
            action="store_true",
            help='print Python traceback on exceptions')
    args = parser.parse_args()

    run(args)

def run(args):
    s = yex.state.State()
    if args.logfile:
        if args.verbose==0:
            args.verbose = 1
        s.controls['tracingonline'].logging_filename = args.logfile
        s.controls['tracingonline'] = 0
    else:
        s.controls['tracingonline'] = 1

    s['_font'].fonts_dir = args.fonts_dir

    if args.verbose!=0:
        for name in s.controls.keys():
            if not name.startswith('tracing'):
                continue
            if name=='tracingonline':
                continue

            s.controls[name] = args.verbose

    try:
        with open(args.source, 'r') as f:
            result = yex.put.put(f)
            print(result)
    except yex.put.PutError as e:
        print(str(e))
        if args.python_traceback:
            traceback.print_exception(
                    None,
                    value=e,
                    tb=e.__traceback__,
                    chain=True,
                    )
        sys.exit(255)

if __name__=='__main__':
    main()
