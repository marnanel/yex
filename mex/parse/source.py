class Source:
    def __init__(self,
            name = None):

        self.name = name
        self.column_number = 1
        self.line_number = 1
        self.push_back = []

        self._iterator = self._read()

    def __iter__(self):
        return self

    def __next__(self):
        if self.push_back:
            result = self.push_back.pop(-1)
            return result
        else:
            try:
                return next(self._iterator)
            except StopIteration:
                return None # eof

    def peek(self):
        result = next(self)
        self.push(result)
        return result

    @property
    def location(self):
        return (
                self,
                self.line_number,
                self.column_number,
                )

    def push(self, v):
        self.push_back.extend([c for c in str(v)])

    def _read(self):
        raise NotImplementedError()

class FileSource(Source):
    def __init__(self,
            f,
            name = None):

        self.f = f

        super().__init__(
                name = name,
                )

    def _read(self):
        self.line_number = 0

        for line in self.f.readlines():

            if self.line_number!=0:
                yield chr(13) # TeX standard; see TeXbook, p46

            self.line_number += 1

            self.column_number = 1

            line = line.rstrip()

            for c in line:
                yield c
                self.column_number += 1


    def __repr__(self):
        return '%s:%4d:%5d' % (
                self.name or 'str',
                self.column_number,
                self.line_number,
                )

class NullSource(Source):
    def _read(self):
        return
        yield
