import sys

class Trace:

    def __init__(self):
        self.streams = [sys.stdout]

    def __call__(self, s):
        """
        Actually emits a tracing record.

        You can monkeypatch this method in testing.
        """

        for stream in self.streams:
            stream.write(f'{s}\n')
            stream.flush()

    @property
    def to_stdout(self):
        return sys.stdout in self.streams

    @to_stdout.setter
    def to_stdout(self, v):
        if v:
            if sys.stdout not in self.streams:
                self.streams.append(sys.stdout)
        else:
            if sys.stdout in self.streams:
                self.streams.remove(sys.stdout)

    def _streams_but_not_stdout(self):
        return [x for x in self.streams if x!=sys.stdout]

    @property
    def target_file(self):
        s = self._streams_but_not_stdout()

        if len(s)==0:
            return None
        elif len(s)==1:
            return s[0]
        else:
            raise ValueError(
                    f"there are {len(s)} file streams")

    @target_file.setter
    def target_file(self, v):
        self.streams = self._streams_but_not_stdout()

        if v is not None:
            self.streams.append(v)

trace = Trace()

__all__ = ['trace']
