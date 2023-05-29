#!/usr/bin/env python
import os
import sys
import subprocess
import select

DEFAULT_PAGER = '/usr/bin/less'

try:
    import fcntl,termios,struct
    data = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, '1234')
    LINES_ON_SCREEN = struct.unpack('hh',data)[0]
except:
    LINES_ON_SCREEN = 25

def run(args, calling_python = True):

    if calling_python:
        args.insert(0, sys.executable)

    print("y: now running:")
    print("y:   " + " ".join(args))

    env = dict(os.environ)
    env['PYTHONPATH'] = '.'
    env['TERM'] = 'screen'

    process = subprocess.Popen(
            args=args,
            env=env,
            stdout=subprocess.PIPE,
            )

    seen = b''
    while True:
        select.select(
            [process.stdout], [], [],
            )
        buf = process.stdout.read(1)
        if len(buf)==0:
            break

        seen += buf
        try:
            sys.stdout.write(buf.decode('utf-8'))
        except ValueError:
            sys.stdout.write(repr(buf))
        sys.stdout.flush()

    lines_printed = len(seen.split(b'\n'))
    if lines_printed > LINES_ON_SCREEN:
        pager = os.environ.get('PAGER', DEFAULT_PAGER)
        print(
                f'printed: {lines_printed} > '
                f'screen height: {LINES_ON_SCREEN}; '
                f'spawning pager {pager}')

        subprocess.run(
                args=[pager,
                    '-R', # enable colour (on less, anyway)
                    ],
                input=seen,
                )

    return process.returncode

def run_tests(log_level, args):
    a = ['-m',
        'pytest',
        f'--log-level={log_level}',
        '--color=yes',
        '-s',
        ]
    a.extend(args)
    result = run(a)
    print("result:", result)

def show_usage_banner():
    print("""y - run yex without installing

    y                   - shows this help
    y -                 - runs yex with no arguments
    y test              - runs the test suite
    y test <testname>   - runs all tests with a name containing <testname>;
                            this turns on debug logging and so on
    anything else       - runs yex with those arguments
    """)

def main():
    if len(sys.argv)==1:
        show_usage_banner()
    elif len(sys.argv)==2 and sys.argv[1]=='-':
        run(['-m', 'yex'])
    elif len(sys.argv)>=2 and sys.argv[1]=='test':
        if len(sys.argv)==3 and not sys.argv[2].startswith('-'):
            run_tests(
                    log_level='DEBUG',
                    args = ['-vv', '-k', sys.argv[2]],
                    )
        else:
            run_tests(
                    log_level='WARN',
                    args=sys.argv[1:],
                    )
    else:
        args = ['-m', 'yex']
        args.extend(sys.argv[1:])
        run(args)

if __name__=='__main__':
    main()
