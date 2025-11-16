from typing import Self, Any

class Location:
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

    """
    A location is the position of a character in a file. We record it
    for each [token](yex.parse.Token.md), so that we can show it in
    error and status messages.

    The available subclasses handle:

    - [text files](yex.parse.FileSource.md)
    - [strings](yex.parse.StringSource.md)
    - [lists](yex.parse.ListSource.md)
    - and [null](yex.parse.NullSource.md).

    Attributes:
        name (Union[str, None]): A name for this source,
            which appears in logs and error messages.
        filename (str): The name of the file, or
            some sort of placeholder like `"<stdin>"`.
        line (int): Line number (aka row number). The first line is 1.
            If this field is zero, we haven't begin reading yet.
        column (int): Column number. The first column is 1.
    """

    def __init__(self,
                 filename,
                 line,
                 column,
                 ):

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

    def __getstate__(self) -> Any:
        return repr(self)

    def __setstate__(self, state:dict):
        self._filename, self._line, self._column = self._parse_serial(state)

    @classmethod
    def from_serial(cls, state:dict) -> Self:
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
    def _parse_serial(cls, serial:str) -> (str, int, int):
        filename, line, column = serial.split(':')
        return filename, int(line), int(column)
