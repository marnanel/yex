class Location:

    def __init__(self,
            filename, line, column):

        self._filename = filename
        self._line = line
        self._column = column

    @property
    def filename(self):
        return self._filename

    @property
    def line(self):
        return self._line

    @property
    def column(self):
        return self._column

    def __repr__(self):
        return '%s:%s:%s' % (
                self._filename,
                self._line,
                self._column,
                )

    def __getstate__(self):
        return repr(self)

    def __setstate__(self, state):
        self._filename, self._line, self._column = self._parse_serial(state)

    @classmethod
    def from_serial(cls, state):
        result = cls(
            *(cls._parse_serial(state)),
            )

        return result

    def __eq__(self, other):
        if not isinstance(other, Location):
            return False

        return self._filename==other._filename and \
                self._line==other._line and \
                self._column==other._column

    @classmethod
    def _parse_serial(cls, serial):
        filename, line, column = serial.split(':')
        return filename, int(line), int(column)
