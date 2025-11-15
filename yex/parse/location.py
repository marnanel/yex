from typing import Self, Any

class Location:
    """
    A location is the position of a character in a file. We record it
    for each [token](yex.parse.Token.md), so that we can show it in
    error and status messages.

    Attributes:
        filename (str): The name of the file, or
            some sort of placeholder like `"&lt;stdin&gt;"`.
        line (int): Line number (aka row number). The first line is 1.
            If this field is zero, we haven't begin reading yet.
        column (int): Column number. The first column is 1.
    """

    def __init__(self,
                 filename: str,
                 line: int,
                 column: int,
                 ):

        self._filename = filename
        self._line = line
        self._column = column

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def line(self) -> int:
        return self._line

    @property
    def column(self) -> int:
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
