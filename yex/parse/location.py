class Location:

    def __init__(self,
            filename, line, column):

        self.filename = filename
        self.line = line
        self.column = column

    def __repr__(self):
        return '%s:%s:%s' % (
                self.filename,
                self.line,
                self.column,
                )

    def __getstate__(self):
        return repr(self)

    def __setstate__(self, state):
        self.filename, self.line, self.column = self._parse_serial(state)

    @classmethod
    def from_serial(cls, state):
        result = cls(
            *(cls._parse_serial(state)),
            )

        return result

    def __eq__(self, other):
        if not isinstance(other, Location):
            return False

        return self.filename==other.filename and \
                self.line==other.line and \
                self.column==other.column

    @classmethod
    def _parse_serial(cls, serial):
        filename, line, column = serial.split(':')
        return filename, int(line), int(column)
