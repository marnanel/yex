import logging
import os

macro_logger = logging.getLogger('mex.macros')

class Filename:
    """
    The name of a file on disk.
    """

    def __init__(self,
            name,
            filetype = None,
            ):
        """
        "name" can be a string, in which case it's the
        name of the file, or a Tokeniser, in which case
        the name of the file is read from it.

        "filetype" is the extension of the file we're
        looking for, or "none" for no extension.
        If it's "font", it will match any font we can
        handle.

        If the filename is read from tokens, and it
        doesn't contain a dot, and "filetype" is not None,
        a dot and "filetype" are appended to the name.
        """

        self.filetype = filetype

        if isinstance(name, str):
            self.tokens = None
            self.value = name
            return

        self.tokens = name
        self.value = ''

        self.tokens.eat_optional_spaces()

        for c in self.tokens:
            if c.category in (c.LETTER, c.OTHER):
                macro_logger.debug("filename character: %s",
                        c)
                self.value += c.ch
            else:
                self.tokens.push(c)
                break

        if self.value=='':
            raise ValueError("no filename found")

        if '.' not in self.value and self.filetype is not None:
            self.value = f"{self.value}.{self.filetype}"

        macro_logger.info("Filename is: %s", self.value)

    @property
    def path(self):
        return os.path.abspath(self.value)
