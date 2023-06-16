import os
import sys
import subprocess
import pytest

class Pager():
    def __init__(self):
        self.original_stdout = sys.stdout
        self.lines = []
        self.pager = None
        self.tried_pager = False

    def isatty(self):
        return False

    def flush(self):
        self.original_stdout.flush()

    def write(self, what):

        if self.pager:
            self.pager.communicate(input=what)
        else:
            self.original_stdout.write(repr(what))
            self.lines.append(what.split('\n'))

            if not self.tried_pager and len(self.lines)>25:
                self.pager = subprocess.Popen(
                        args=['/usr/bin/less', '-'],
                        text=True,
                        stdout=self.original_stdout,
                        )
                self.pager.communicate(input='\n'.join(lines))

def main():
    print(sys.argv)
    if len(sys.argv)==1:
        args = []
    elif len(sys.argv)==2 and not sys.argv[1].startswith('-'):
        args = ['-svv', '--log-level=DEBUG', '-k', sys.argv[1]]
    else:
        args = sys.argv[1:]

    print(args)
    print(os.environ.get('PAGER', None))

    output = Pager()
    sys.stdout = output

    pytest.main(args)

if __name__=='__main__':
    main()
