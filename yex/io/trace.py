import sys

DEFAULT_DEFAULT_LOG_FILENAME = 'yex.log'

class Trace:

    def __init__(self):
        self.streams = [sys.stdout]
        self.default_log_filename = DEFAULT_DEFAULT_LOG_FILENAME

    def __call__(self, s):
        """
        Actually emits a tracing record.

        You can monkeypatch this method in testing.
        """

        for stream in self.streams:
            stream.write(s)
            stream.write('\n')
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

    @property
    def target_file(self):
        s = [x for x in self.streams if x!=sys.stdout]

        if len(s)==0:
            return None
        elif len(s)==1:
            return s[0]
        else:
            raise ValueError(
                    f"there are {len(s)} file streams")

    @target_file.setter
    def target_file(self, v):
        self.streams = [x for x in self.streams if x==sys.stdout]

        if v is not None:
            assert hasattr(v, 'write'), v
            self.streams.append(v)

    @property
    def to_file(self):
        return self.target_file is not None

    @to_file.setter
    def to_file(self, v):
        assert isinstance(v, bool)
        if v:
            self.target_file = open(self.default_log_filename, 'w')
        else:
            self.target_file = None

    def __str__(self):
        result = '[trace;'
        for s in self.streams:
            try:
                result += s.name + ';'
            except Exception as e:
                result += str(e) + ';'

        result = result[:-1]+']'
        return result

trace = Trace()

__all__ = ['trace']
