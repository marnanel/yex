class Source:
    def __init__(self,
            name = None):

        self.name = name
        self.column_number = 1

        self._iterator = self._read()

    def __iter__(self):
        return self

    def __next__(self):
        return self._iterator.__next__()

    @property
    def location(self):
        return (
                self,
                self.line_number,
                self.column_number,
                )

    @property
    def line_number(self):
        raise NotImplementedError()

    def _read(self):
        raise NotImplementedError()

class FileSource(Source):
    def __init__(self,
            source,
            name = None):

        self.source = source
        self.lines = []

        super().__init__(
                name = name,
                )

    def _read(self):
        for line in self.source.readlines():

            self.column_number = 1
            self.lines.append(line)

            for c in line:
                yield c
                self.column_number += 1

    @property
    def line_number(self):
        return len(self.lines)

    def __repr__(self):
        return '%s:%4d:%5d' % (
                self.name or 'str',
                self.column_number,
                self.line_number,
                )

class NullSource(Source):
    @property
    def line_number(self):
        return 1

    def _read(self):
        return
        yield
