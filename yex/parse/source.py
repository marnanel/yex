import yex
import logging

logger = logging.getLogger('yex.general')

# TeX standard; see TeXbook, p46
NEWLINE = chr(13)

SPIN_LIMIT = 1000

class Source:
    def __init__(self,
            name = None):

        self.name = name
        self.column_number = 1
        self.line_number = 0
        self.current_line = ''
        self.spin_check = 0
        self.exhaust_at_eol = False
        self.line_number_setter = None

        # Start with a dummy blank line, because lines in a file are
        # counted from 1.
        self.lines = ['']

        self._iterator = self._read()

        logger.debug("%s: ready",
                self)

    def __iter__(self):
        return self

    def __next__(self):

        self.spin_check += 1
        if self.spin_check >= SPIN_LIMIT:
            raise yex.exception.SpinButStillError(
                count = self.spin_check,
                )

        if self._iterator is None:
            return None

        self.spin_check = 0

        while self.column_number>=len(self.current_line):
            self._get_next_line()

            if self._iterator is None:
                # all done!
                return None

        result = self.current_line[self.column_number]
        self.column_number += 1
        logger.debug("%s: returning %s",
                self, result)
        return result

    def _get_next_line(self):

        if self.exhaust_at_eol:
            logger.debug("%s: exhaust_at_eol is set; we must stop now",
                    self)
            self._iterator = None
            return

        try:
            self.current_line = next(self._iterator)
            self.column_number = 0
            self.lines.append(self.current_line)

            if self.line_number is not None:
                self.line_number += 1
                if self.line_number_setter is not None:
                    self.line_number_setter(self.line_number)

            logger.debug("%s: got new line: %s",
                    self,
                    self.current_line)

        except StopIteration:
            logger.debug("%s: eof",
                    self)
            self._iterator = self.column_number = None

    def discard_rest_of_line(self):
        if self.column_number != len(self.current_line):
            logger.debug("%s: discarding the rest of the line (it was %s)",
                    self, repr(self.current_line[self.column_number:]))
        self._get_next_line()

    @property
    def location(self):
        return yex.parse.Location(
                filename = self.name,
                line = self.line_number or 0,
                column = self.column_number or 0,
                )

    def _read(self):
        raise NotImplementedError()

    def __repr__(self):
        return '[%s;%s;l=%d;c=%d]' % (
                self.__class__.__name__,
                self.name or '?',
                self.line_number or 0,
                self.column_number or 0,
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

            yield line + NEWLINE

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
            yield line + NEWLINE
        logger.debug("%s: string reader out of lines",
                self)

class ListSource(Source):
    def __init__(self,
            contents,
            name = None):

        super().__init__(
                name = name or '<list>',
                )

        self.contents = []

        for item in list(contents):
            if isinstance(item, str) and len(item)>1:
                self.contents.extend([x for x in item])
            else:
                self.contents.append(item)

        logger.debug("%s:   -- list is: %s",
                self, contents)

        self.contents = contents
        self.column_number = 0
        self.line_number = None

    def _read(self):
        yield self.contents

class NullSource(Source):
    def _read(self):
        logger.debug("%s: null reader out of lines "
                "(obviously)",
                self)
        return
        yield
