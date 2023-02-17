import os
import yex
import logging
from yex.parse.pushback import Pushback

logger = logging.getLogger('yex.general')

class InputStream:
    """
    A stream for input.

    Most of this behaviour is specified on p215 of the TeXbook.
    """

    def __init__(self, doc, number, filename):

        self.doc = doc
        self.number = number
        self.identifier = f'_inputs;{number}'
        self.is_queryable = False

        logger.debug("%s: opening %s", self, filename)

        try:
            filename = yex.filename.Filename(
                    name = filename,
                    default_extension = 'tex',
                    ).resolve()

            self.f = iter(open(filename, 'r'))

            logger.debug("%s: opened %s", self, filename)
            self.eof = False
        except FileNotFoundError:
            self.f = None
            logger.debug("%s: %s doesn't exist", self, filename)
            self.eof = True

    def open(self, filename):
        return self.doc['_inputs'].open(
                number = self.number,
                filename = filename)

    def read(self, varname=None):
        r"""
        Reads a line from the input, tokenises it, and
        returns the result. Keeps reading lines until
        the curly brackets balance.

        Args:
            varname (bool): only used in the subclass.
        """

        if self.f is None:
            return None

        def file_contents():
            try:
                while True:
                    line = next(self.f)

                    logger.debug("%s: next line is: %s",
                            self, repr(line))

                    yield line

            except StopIteration:
                logger.debug("%s: out of lines; yielding fake last line",
                        self)
                self.eof = True
                self.f = None
                yield '\r'

        result = []
        pushback = Pushback()

        for line in file_contents():

            tokeniser = yex.parse.Tokeniser(
                    doc = self.doc,
                    source = line,
                    pushback = pushback,
                    )

            t = ''
            while t is not None:
                t = next(tokeniser)

                if pushback.group_depth < 0:
                    # balanced brackets
                    return result
                elif t is not None:
                    result.append(t)

            logger.debug("%s: found %s; group_depth==%s",
                    self, result, pushback.group_depth)

            if pushback.group_depth==0:
                break

        return result

    def __repr__(self):
        try:
            if self.f is None:
                return '[input;closed]'

            return f'[input;f={repr(self.f.name)}]'
        except:
            return f'[input;f=?]'

    def close(self):
        self.doc['_inputs'].close(self.number)

    def _actually_close(self):
        logger.debug("%s: closing", self)
        if self.f is not None:
            self.f.close()
            self.f = None
        self.eof = True

    @classmethod
    def on_terminal(cls, doc, number):
        return TerminalInputStream(doc, number)

class TerminalInputStream(InputStream):

    def __init__(self,
            doc,
            number = 0,
            ):

        self.doc = doc
        self.number = number
        self.identifier = f'_inputs;{number}'
        self.show_variable_names = number>0
        self.eof = True
        self.is_queryable = False

        class ReadTerminal:
            def __iter__(self):
                return self

            def __next__(self):
                result = input()
                logger.debug("%s: received from terminal: %s",
                        self, result)
                return result

        self.f = ReadTerminal()

    def read(self,
            varname=None):
        if self.show_variable_names and varname is not None:
            print(fr'{varname}=', end='', flush=True)

        return super().read()

    def _actually_close(self):
        logger.debug("%s: 'close' called; ignoring", self)

    def __repr__(self):
        if self.show_variable_names:
            return '[input;f=terminal;show vars]'
        else:
            return '[input;f=terminal]'
