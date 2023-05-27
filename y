#!/usr/bin/env python
import os
import sys
import subprocess

def run(args, calling_python = True):

    if calling_python:
        args.insert(0, sys.executable)

    print("y: now running:")
    print("y:   " + " ".join(args))

    env = dict(os.environ)
    env['PYTHONPATH'] = '.'
    subprocess.run(args=args, env=env)

def run_tests(log_level, args):
    a = ['-m',
        'pytest',
        f'--log-level={log_level}',
        '-s',
        ]
    a.extend(args)
    run(a)

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
