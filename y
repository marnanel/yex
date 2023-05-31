#!/usr/bin/env python
import os
import sys
import subprocess
from threading import Thread, Event
from queue import Queue, Empty

DEFAULT_PAGER = '/usr/bin/less'

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

    queue = Queue()
    thread = Thread(target=enqueue_output, args=(process.stdout, queue))
    thread.daemon = True
    thread.start()

    seen = b''
    lines_count = 0

    seen_test_error_line = False

    while True:
        line = queue.get()
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

def run_tests(log_level, args):
    a = ['-m',
        'pytest',
        f'--log-level={log_level}',
        '--color=yes',
        '-s',
        ]
    a.extend(args)
    result = run(a)

    if result:
        print("y: result:", result)

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
