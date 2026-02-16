#!/usr/bin/env python
import os
import sys
import subprocess
import argparse
from threading import Thread, Event
from queue import Queue, Empty

DEFAULT_PAGER = '/usr/bin/less'
DEFAULT_YEX_LOGGERS = 'all,parse'

try:
    import fcntl,termios,struct
    data = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, '1234')
    LINES_ON_SCREEN = struct.unpack('hh',data)[0]
except:
    LINES_ON_SCREEN = 25

too_spammy = Event()

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
        if too_spammy.is_set():
            queue.put(out.read())
            break

    queue.put(None)

def run(args, verbose = False, calling_python = True):

    if calling_python:
        args.insert(0, sys.executable)

    loggers = DEFAULT_YEX_LOGGERS

    if verbose:
        loggers = f'verbose,{loggers}'

    extra_env = {
            'PYTHONPATH': '.',
            'TERM': 'screen',
            'YEX_LOGGERS': loggers,
            }

    print("y: now running:")
    print("y:   " +
          (''.join([f'{k}={v} ' for k,v in extra_env.items()])) +
          (" ".join(args))
           )

    process = subprocess.Popen(
            args=args,
            env=os.environ | extra_env,
            stdout=subprocess.PIPE,
            )

    queue = Queue()
    thread = Thread(target=enqueue_output, args=(process.stdout, queue))
    thread.daemon = True
    thread.start()

    seen = b''
    lines_count = 0

    seen_test_error_line = False

    while True:
        line = queue.get()

        if line is None:
            break

        seen += line

        if b'______' in line:
            seen_test_error_line = True

        lines_count += 1

        if too_spammy.is_set():
            if queue.qsize()==0:
                break
        else:

            if seen_test_error_line and lines_count > LINES_ON_SCREEN:
                sys.stdout.write('\n\n  (Stand by...)\n')
                too_spammy.set()
                thread.join()

                try:
                    seen += queue.get_nowait()
                except Empty:
                    pass

            try:
                sys.stdout.write(line.decode('utf-8'))
            except ValueError:
                sys.stdout.write(repr(line))
            sys.stdout.flush()

    lines_printed = len(seen.split(b'\n'))
    if lines_printed > LINES_ON_SCREEN:
        pager = os.environ.get('PAGER', DEFAULT_PAGER)

        subprocess.run(
                args=[pager,
                    '-R', # enable colour (on less, anyway)
                    ],
                input=seen,
                )

    return process.returncode

def run_tests(args, verbose):
    a = ['-m',
        'pytest',
        '--color=yes',
        '-s',
        ]
    a.extend(args)
    result = run(a, verbose=verbose)

    if result:
        print("y: result:", result)

def run_run():
    print('run')

def run_test():
    print('test')

def run_compare():
    print('compare')

# TODO test -> --test
# TODO --compare, with previous git version, defaulting to HEAD^
def show_usage_banner():
    print("""y - run yex without installing

    y                   - shows this help
    y -                 - runs yex with no arguments
    y test              - runs the test suite
    y test <testname>   - runs all tests with a name containing <testname>;
                            this turns on debug logging and so on
    anything else       - runs yex with those arguments
    """)

def parse_opts():
    parser = argparse.ArgumentParser(
            prog = 'y',
            description = 'run yex without installing, or run tests',
            )
    subparsers = parser.add_subparsers(
            help = 'what to do',
            required = True,
            )

    subparser_run = subparsers.add_parser(
            'run',
            help = 'run yex without installing',
            )
    subparser_run.add_argument(
            'args', nargs='*', help='arguments to pass to yex',
            )
    subparser_run.set_defaults(func=run_run)

    subparser_test = subparsers.add_parser(
            'test',
            help = 'run a test with logging',
            )
    subparser_test.add_argument(
            'name', help='substring of names of the tests to run',
            default = '',
            )
    subparser_test.set_defaults(func=run_test)

    subparser_compare = subparsers.add_parser(
            'compare',
            help = 'compare test results against a previous commit',
            )
    subparser_compare.set_defaults(func=run_compare)

    args = parser.parse_args()
    return args

def main():
    args = parse_opts()
    args.func()
    return
    if len(sys.argv)==1:
        show_usage_banner()
    elif len(sys.argv)==2 and sys.argv[1]=='-':
        run(['-m', 'yex'])
    elif len(sys.argv)>=2 and sys.argv[1]=='test':
        if len(sys.argv)==3 and not sys.argv[2].startswith('-'):

            args = ['-vv']

            if not sys.argv[2].endswith('.py'):
                args.append('-k')

            args.append(sys.argv[2])

            run_tests(
                    verbose = True,
                    args = args,
                    )
        else:
            run_tests(
                    verbose = False,
                    args=sys.argv[1:],
                    )
    else:
        args = ['-m', 'yex']
        args.extend(sys.argv[1:])
        run(args)

if __name__=='__main__':
    main()
