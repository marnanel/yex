from collections import defaultdict
import logging

logger = logging.getLogger('mex.general')

# TeX standard; see TeXbook, p46
NEWLINE = chr(13)

class Source:
    def __init__(self,
            name = None):

        self.name = name
        self.column_number = 1
        self.line_number = 0
        self.current_line = ''
        self.push_back = []

        self.lines = []

        self._iterator = self._read()

        logger.debug("%s: ready",
                self)

    def __iter__(self):
        return self

    def __next__(self):

        if self.push_back:
            result = self.push_back.pop(-1)

            logger.debug("%s: from pushback: %s",
                    self, result)

            return result

        if self._iterator is None:
            return None

        if self.column_number>=len(self.current_line):
            try:
                self.current_line = next(self._iterator) + NEWLINE
                self.line_number += 1
                self.column_number = 0
                self.lines.append(self.current_line)

                logger.debug("%s: got new line: %s",
                        self,
                        self.current_line)

            except StopIteration:
                logger.debug("%s: eof",
                        self)
                self._iterator = None
                return None

        result = self.current_line[self.column_number]
        self.column_number += 1
        logger.debug("%s: returning %s",
                self, result)
        return result

    def peek(self):
        result = next(self)
        self.push(result)
        return result

    @property
    def location(self):
        return (
                self.line_number,
                self.column_number,
                )

    def push(self, v):
        if v is None:
            return

        self.push_back.extend(reversed([c for c in v]))

        logger.debug("%s: push: %s",
                self, self.push_back)

    def _read(self):
        raise NotImplementedError()

    def __repr__(self):
        return '[%s;%s;l=%d;c=%d]' % (
                self.__class__.__name__,
                self.name or '?',
                self.line_number,
                self.column_number,
                )

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

            logger.debug("%s read line: %s",
                    self, line)

            line = line.rstrip(' \r\n')

            yield line

        logger.debug("%s: file reader out of data",
                self)

class StringSource(Source):
    def __init__(self,
            string,
            name = None):

        super().__init__(
                name = '<str>',
                )
        self.string = string
        logger.debug("%s: string is: %s",
                self, string)

    def _read(self):
        for line in self.string.splitlines():
            yield line
        logger.debug("%s: string reader out of lines",
                self)

class NullSource(Source):
    def _read(self):
        logger.debug("%s: null reader out of lines "
                "(obviously)",
                self)
        return
        yield
