class Source:
    def __init__(self,
            source,
            name = None):

        self.source = source
        self.name = name
        self.lines = []
        self.column_number = 1

        self._iterator = self._read()

    def __iter__(self):
        return self

    def __next__(self):
        return self._iterator.__next__()

    def _read(self):
        for line in self.source.readlines():

            self.column_number = 1
            self.lines.append(line)

            for c in line:
                yield c
                self.column_number += 1

    @property
    def row_number(self):
        return len(self.lines)
