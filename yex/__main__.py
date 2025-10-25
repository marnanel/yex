import argparse
import os
import sys
import yex
import yex.put
import traceback
import yex.logging

logger = yex.logging.getLogger('main')

DEFAULT_OUTPUT_DRIVER = 'html'

args = None

def main():

    global args

    parser = argparse.ArgumentParser(
            prog = 'yex',
            description='typeset beautifully',
            )

    parser.add_argument('source',
                        help='source filename',
                        default = None,
                        nargs = '?',
                        )
    parser.add_argument('--verbose', '-v',
            action="count", default=0,
            help='turn on all tracing')
    parser.add_argument('--loggers', '-l',
                        help=(
                            'which loggers to turn on; '
                            'give a comma-separated list; '
                            '"all" for all but those listed; '
                            '"none" for none; '
                            '"list" shows a list, then exits; '
                            f'default is "{yex.logging.DEFAULT}".'
                            ),
                        default = None,
                        )
    parser.add_argument('--logfile', '-L',
            default=None,
            help='log filename (implies -v); default "yex.log"')
    parser.add_argument('--fonts-dir', '-f',
            default='other',
            help='directory with fonts in')
    parser.add_argument('--output', '-o',
            help='output filename')

    debugging_group = parser.add_argument_group(
            title="debugging",
            description="for fixing problems in yex itself")
    debugging_group.add_argument('--bare', '-B',
            action='store_true',
            help='run without loading the plain.tex stylesheet')
    debugging_group.add_argument('--dump', '-d',
            action='store_true',
            help='dump state of system instead of producing output')
    debugging_group.add_argument('--dump-full', '-D',
            action='store_true',
            help=('dump EVERYTHING about the state of the system '
                'instead of producing output'),
            )
    debugging_group.add_argument('--python-traceback', '-P',
            action="store_true",
            help='print Python traceback on exceptions')
    debugging_group.add_argument('--profiling', '-p',
            action='store',
            help=f'profile, and output the data to the named file',
            )

    args = parser.parse_args()

    if args.profiling is not None:
        import cProfile
        cProfile.run('run()', args.profiling)
    else:
        run()

def _parse_output_filename(source, output):

    if output is None:
        source_root, source_ext = os.path.splitext(source)
        output_format = DEFAULT_OUTPUT_DRIVER
        output_filename = f'{source_root}.{output_format}'
    else:
        output_root, output_ext = os.path.splitext(output)
        output_format = output_ext[1:]
        output_filename = output

    return output_format, output_filename

def run():
    if args.verbose:
        args.loggers += ',verbose'

    yex.logging.selectLoggers(
            handlers = args.loggers,
            )

    if args.source is None:
        print('yex: I need an input filename')
        sys.exit(254)

    if args.bare:
        style = yex.style.Bare
    else:
        style = yex.style.Plain

    s = yex.Document(
            style=style,
            )

    if args.logfile:
        s.controls[r'\tracingonline'].logging_filename = args.logfile
        s.controls[r'\tracingonline'] = 0

    output_format, output_filename = _parse_output_filename(
            source = args.source,
            output = args.output,
            )

    s['_font'].fonts_dir = args.fonts_dir

    try:
        with open(args.source, 'r') as f:
            result = yex(f,
                         doc = s,
                         target = output_filename,
                         target_format = output_format,
                         dump = args.dump,
                         dump_full = args.dump_full,
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
