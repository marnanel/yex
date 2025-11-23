import sys

DEFAULT_DEFAULT_LOG_FILENAME = 'yex.log'

class Trace:
    """
    Implementation of TeX's tracing system.

    This is a singleton class; you should access it as `yex.io.trace`.

    See also the handlers in `yex.keyword.trace`.

    Fields:
        default_log_filename (str): the filename which will be used
            if you set `to_file` to `True`.
        streams (list): open streams to write trace messages to.
    """

    def __init__(self):
        self.streams = [sys.stdout]
        self.default_log_filename = DEFAULT_DEFAULT_LOG_FILENAME

    def __call__(self, s):
        """
        Emits a tracing record to all streams in `self.streams`.

        Args:
            s (str): what to output. A newline will be added.
        """

        for stream in self.streams:
            stream.write(s)
            stream.write('\n')
            stream.flush()

    @property
    def to_stdout(self):
        """
        Whether tracing is going to `sys.stdout` (`bool`).

        This is based on an interpretation of `self.streams`.
        It uses the value of `sys.stdout` at the time you
        call it.
        """
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
        """
        What stream the tracing is going to, other than `sys.stdout`.
        Can be None.

        This is based on an interpretation of `self.streams`.
        It uses the value of `sys.stdout` at the time you
        call it.

        Setting this field removes all other non-stdout streams
        from `self.streams`.

        Raises:
            ValueError: on get, if there are multiple
                streams in `self.streams` which aren't `sys.stdout`.
            TypeError: on put, if set to a value which
                is not file-like.
        """
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
            if not hasattr(v, 'write'):
                raise TypeError(v)
            self.streams.append(v)

    @property
    def to_file(self):
        """
        Whether tracing is going to a stream other than `sys.stdout`
        (`bool`).

        This is based on an interpretation of `self.streams`.
        It uses the value of `sys.stdout` at the time you
        call it.

        If you set this value to `True`, then we open a file
        called `self.default_log_filename` for writing.

        Raises:
            TypeError: on put, if set to a value which
                is not boolean. This is to catch you if you
                get this field mixed up with `target_file`.
        """
        try:
            return self.target_file is not None
        except ValueError:
            return True

    @to_file.setter
    def to_file(self, v):
        if not isinstance(v, bool):
            raise TypeError(v)
        elif v:
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
