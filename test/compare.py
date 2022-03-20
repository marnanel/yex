import argparse
import subprocess
import tempfile
import os
import yex.__main__
import logging


class LogHandler(logging.Handler):
    def __init__(self,
            level = logging.NOTSET):
        super().__init__(level)

        self.records = []

    def emit(self, record):
        self.records.append(record)

def copy_in(source,
        target_dir):

    base_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            )

    for name in source:
        with open(
                os.path.join(
                    base_dir,
                    name),
                'rb') as f:
            contents = f.read()

        with open(
                os.path.join(
                    target_dir,
                    os.path.basename(name),
                    ),
                'wb') as f:
            f.write(contents)

def examine_tex(code, binary,
        traces = ['commands']):

    with tempfile.TemporaryDirectory(prefix='yexcompare_') as d:
        os.chdir(d)
        with open('compare.tex', 'w') as source:
            for trace in traces:
                source.write(rf'\tracing{trace} 1' + '\n')
            source.write(code + '\n')

        output = subprocess.run(
                [
                    binary,
                    '-interaction=batchmode',
                    'compare.tex',
                    ],
                capture_output = True,
                )

        log = [x[:-1]
                for x in
                open('compare.log', 'r').readlines()]

        if log[0].startswith('This is TeX'):
            log = log[1:]

        try:
            emergency_stop = log.index('! Emergency stop.')
            log = log[:emergency_stop]
        except ValueError:
            pass

        return log

def examine_yex(code,
        traces = ['commands']):

    with tempfile.TemporaryDirectory(prefix='yexcompare_') as d:

        log_handler = LogHandler(level=logging.DEBUG)

        for tracer in traces:
            logger = logging.getLogger(f'yex.{tracer}')
            logger.propagate = False
            logger.addHandler(log_handler)

        copy_in(
                [
                    'other/cmr10.tfm',
                ],
                d)

        os.chdir(d)

        with open('compare.tex', 'w') as source:
            for trace in traces:
                source.write(rf'\tracing{trace} 1' + '\n')
            source.write(code + '\n')

        class FakeParams:
            def __init__(self, **kwargs):
                self.contents = kwargs

            def __getattr__(self, f):
                return self.contents[f]

        try:
            yex.__main__.run(
                    FakeParams(
                        logfile = None,
                        verbose = 0,
                        source = 'compare.tex',
                        fonts_dir = '',
                        python_traceback = True,
                        ))
        except Exception as e:
            raise e

        return [r.getMessage() for r in log_handler.records]

def dump_list(title, contents):
    print(title)
    for i, line in enumerate(contents):
        print('%04d - %s' % (i, line))
    print()

def main():
    parser = argparse.ArgumentParser(
            description='compare yex and TeX',
            )

    args = parser.parse_args()

    code = r"Hello world"

    tex = examine_tex(
            code = code,
            binary = '/usr/bin/tex')

    dump_list('TeX', tex)

    yex = examine_yex(
            code = code,
            )

    dump_list('yex', yex)

if __name__=='__main__':
    main()
