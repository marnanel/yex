import argparse
import sys
import yex.put
import yex.document
import traceback
import logging

logger = logging.getLogger('yex.general')

def main():
    parser = argparse.ArgumentParser(
            prog = 'yex',
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
    s = yex.Document()

    if args.logfile:
        s.controls[r'\tracingonline'].logging_filename = args.logfile
        s.controls[r'\tracingonline'] = 0

    s['_font'].fonts_dir = args.fonts_dir

    if args.verbose>1:
        logger.setLevel(logging.DEBUG)
    elif args.verbose>0:
        logger.setLevel(logging.INFO)

    try:
        with open(args.source, 'r') as f:
            result = yex.put.put(f,
                    target = 'yex.svg', # FIXME
                    )
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
