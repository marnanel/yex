import sys

class Trace:
    def __call__(self, s):
        sys.stdout.write(f'{s}\n')
        sys.stdout.flush()

trace = Trace()

__all__ = ['trace']
