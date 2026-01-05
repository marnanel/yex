import yex
import yex.logging
from typing import Union, Callable, List, Any

logger = yex.logging.getLogger('parse')

# TeX standard; see TeXbook, p46
NEWLINE = chr(13)

class Source:
    """
    A source is an iterator providing characters.
    A [tokeniser](yex.parse.Tokeniser.md) reads characters
    from the source, and forms them into [tokens](yex.parse.Token.md).

    The available subclasses handle:

    - [text files](yex.parse.FileSource.md)
    - [strings](yex.parse.StringSource.md)
    - [lists](yex.parse.ListSource.md)
    - and [null](yex.parse.NullSource.md).

    Attributes:
        name (Union[str, None]): A name for this source,
            which appears in logs and error messages.
        line_number (int): The line number (also called the row number).
            The first line is 1. If the line number is 0,
            we haven't started reading yet.
        column (int): The column number. The first column is 1.
        spin_check (int): How many times we've carried out a "read" operation
            without moving forwards. If this reaches Source.SPIN_LIMIT,
            then we throw [SpinButStillError](yex.Exception.md).
        current_line (str): The contents of the current line
            we're working through.  We keep the whole line until
            we're done with it, so that we can show it in
            error messages.
        exhaust_at_eol (bool): If this is True, we act as though
            the end of the current line is the end of file.
            This is rarely needed: it's useful when
            we're reading input line by line from the terminal.
        line_number_setter (Union[Callable, None]):
            If this is not None, we call it every time we begin a new line,
            with the line number as the single argument.
        peeked (List[str]): When someone uses our peek() method,
            we have to read the next character in order to know what
            to tell them. In order to maintain the illusion that the
            peeked character is still in the future, we push it onto this list.
            It follows that this list may only ever have zero or one members.
        tail (str): The most recent ten characters (or fewer, if we haven't
            yet seen ten). This is only used by the "position" logger.
            Characters with a codepoint below 33 are represented by
            their counterparts in the Unicode block
            ["Control Pictures"](https://www.unicode.org/charts/PDF/U2400.pdf),
            starting at U+2400. For example, a space is `␠`.
        lines (List[str]): All the lines we've yet read from the file.
            The last entry in this list will be equal to self.current_line.
            This is wasteful, but useful sometimes.
            The list starts with a dummy blank entry, because lines
            in a file are counted from 1.
        location (yex.parse.Location): Where we are in the file (or whatever),
            as a Location object. The class also provides properties for
            line and column numbers as ints, and the filename as a string.
    """

    SPIN_LIMIT = 1000

    def __init__(self,
                 name = None,
                 ):

        self.name = name
        self.column_number = 1
        self.line_number = 0
        self.current_line = ''
        self.spin_check = 0
        self.exhaust_at_eol = False
        self.line_number_setter = None
        self.peeked = []
        self.tail = ''
        self.lines = ['']
        self._iterator = self._read()

        logger.debug("%s: ready",
                self)

    def __iter__(self):
        return self

    def __next__(self):

        self.spin_check += 1

        if self.spin_check >= self.SPIN_LIMIT:
            raise yex.exception.SpinButStillError(
                count = self.spin_check,
                )
        elif self.peeked:
            result = self.peeked[0]
            self.peeked = []
            return result
        elif self._iterator is None:
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
                self, repr(result))

        self._update_tail(result)

        return result

    def _update_tail(self, s:Any) -> None:
        s = str(s)
        if s<=' ':
            s = chr(0x2400+ord(s))

        self.tail = (self.tail+s)[-10:]

    def peek(self) -> str:
        """
        Returns the character which our iterator will return next time.
        A glimpse into the future!
        """
        if not self.peeked:
            self.peeked.append(next(self))

        return self.peeked[0]

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
                    repr(self.current_line))

        except StopIteration:
            logger.debug("%s: eof",
                    self)
            self._iterator = self.column_number = None

    def discard_rest_of_line(self) -> None:
        """
        Drops the whole of the rest of the current line.
        """
        if self._iterator is None:
            return

        if (
                self.column_number is not None and
                self.column_number != len(self.current_line)):
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
    """
    A [source](yex.parse.Source.md) based on a text file on disk,
    such as a TeX source file.

    Spaces (ASCII 32) at the end of each line are dropped.
    All linefeeds (ASCII 10) and carriage returns (ASCII 13)
    at the end of each line are replaced by a single carriage return.
    The final line will always end with a carriage return.

    Attributes:
        f (TextIO): a filehandle to read from. You should
            probably put the filename, if you have it, in the
            "name" parameter to aid debugging and status
            messages.
    """
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
    """
    A [source](yex.parse.Source.md) based on a string.
    We split the string into lines at linebreaks,
    which are whatever Python's `str.splitlines()`
    thinks they are. We replace them with a single
    carriage return (ASCII 13) at the end of each line,
    including the last line.

    Attributes:
        string (str): a string of characters.
    """

    _EXCERPT_LENGTH = 19
    def __init__(self,
            string,
            name = None):

        if name is None:
            name = string[:self._EXCERPT_LENGTH]
            if len(name)>self._EXCERPT_LENGTH:
                name += '…'
            name = name.replace('\n', '␤')
            name = repr(name)

        super().__init__(
                name = name,
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
    """
    A [source](yex.parse.Source.md) based on a list.
    Generally this is a list of strings, although
    you can use anything you want the tokeniser to find.

    Multi-character strings are split into their
    component characters; any other entries are left
    as-is. For example, if you passed in
    ```
    ['a', 177, 'b', 'fred', 'c']
    ```
    the tokeniser would receive

    - `"a"`
    - `177`
    - `"b"`
    - `"f"`
    - `"r"`
    - `"e"`
    - `"d"`
    - `"c"`

    Attributes:
        contents (List[Any]): the list.
    """
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

    def _update_tail(self, s):
        pass

class NullSource(Source):
    """
    A source providing nothing, no matter how many times
    you ask.

    To consider;
        Is this ever used? It seems to do no more than
        `ListSource([])` would.
    """
    def _read(self):
        logger.debug("%s: null reader out of lines "
                "(obviously)",
                self)
        return
        yield
