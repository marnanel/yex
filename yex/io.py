import os
import yex
import logging

logger = logging.getLogger('yex.general')

class StreamsTable:
    def __init__(self, doc, our_type):
        self.streams = {}
        self.doc = doc
        self.our_type = our_type

    def open(self, number, filename):

        if number>=0 and number<=15:
            try:

                if number in self.streams:
                    if self.streams[number].f is not None:
                        logger.debug("%s: nb: opening new stream over: %s",
                                self, self.streams[number])

                if filename is None:
                    result = self.our_type.on_terminal(
                            doc=self.doc,
                            number=number,
                            )
                    logger.debug("%s: opened %s = terminal",
                            self, number)

                else:
                    result = self.our_type(
                            filename=filename,
                            number=number,
                            doc=self.doc,
                            )
                    logger.debug("%s: opened %s = %s",
                            self, number, repr(filename))

                self.streams[number] = result
            except OSError as ose:
                logger.info(
                        "%s: open of %s = %s failed: %s",
                        self,
                        number,
                        repr(filename),
                        ose,
                        )

            return self[number]

        logger.debug("%s: opened %s = terminal",
                self, number)
        return self.our_type.on_terminal(doc=self.doc, number=number)

    def close(self, number):
        """
        Closes a stream.

        If there is no stream with the given number, does nothing.

        Args:
            number: the number of the stream to close.
        """
        if number not in self.streams:
            logger.debug(("%s: can't close stream %s which we don't have; "
                "doing nothing"),
                self, number)
            return

        logger.debug('%s: closing stream %s (currently %s)',
                self, number, self.streams[number])

        self.streams[number]._actually_close()
        del self.streams[number]

    def __getitem__(self, number):

        if number<0 or number>15:
            logger.debug("%s: returning terminal for stream number %s",
                self, number)
            return self.our_type.on_terminal(doc=self.doc, number=number)

        if number not in self.streams:
            logger.debug('%s: no stream %s; returning terminal',
                self, number)
            return self.open(number=number, filename=None)

        return self.streams[number]

    def __str__(self):
        return f'{self.our_type.__name__} table'

class InputStream:
    """
    A stream for input.

    Most of this behaviour is specified on p215 of the TeXbook.
    """

    def __init__(self, doc, number, filename):

        self.doc = doc
        self.number = number
        self.identifier = f'_inputs;{number}'

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

        brackets_balance = 0

        result = []

        for line in file_contents():

            tokeniser = yex.parse.Tokeniser(
                    doc = self.doc,
                    source = line,
                    )

            for t in tokeniser:
                if t is None:
                    break
                elif isinstance(t, yex.parse.BeginningGroup):
                    brackets_balance += 1
                elif isinstance(t, yex.parse.EndGroup):
                    brackets_balance -= 1
                    if brackets_balance < 0:
                        return result

                result.append(t)

            if brackets_balance==0:
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
        self.eof = False

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

class OutputStream:

    def __init__(self, doc, number, filename):

        self.doc = doc
        self.number = number
        self.identifier = f'_outputs;{number}'

        logger.debug("%s: opening %s", self, filename)

        if filename is None:
            self.f = None
            return

        filename = yex.filename.Filename(
                name = filename,
                default_extension = 'tex',
                )

        self.f = open(filename, 'w')
        logger.debug("%s: opened %s", self, filename)

    def open(self, filename):
        return self.doc['_outputs'].open(
                number = self.number,
                filename = filename)

    def write(self, s):
        logger.debug("%s: writing: %s", self, repr(s))

        if self.f is None:
            logger.debug("%s: but the stream is closed", self)
            raise ValueError("the stream is closed")

        self.f.write(s)
        self.f.flush()

    def close(self):
        self.doc['_outputs'].close(self.number)

    def _actually_close(self):
        logger.debug("%s: closing", self)
        if self.f is not None:
            self.f.close()
            self.f = None

    def __repr__(self):
        try:
            if self.f is None:
                return f'[{self.identifier};closed]'

            return f'[{self.identifier};f={repr(self.f.name)}]'
        except:
            return '[output;f=?]'

    @classmethod
    def on_terminal(cls, doc, number):
        return TerminalOutputStream(doc, number)

class TerminalOutputStream(OutputStream):

    def __init__(self, doc, number):
        self.doc = doc
        self.number = number
        self.identifier = f'_inputs;{number}'
        self.only_on_log = number<0
        self.f = None

    def write(self, s):
        for line in s.split('\r'):
            logger.info("Log: %s", line)
        if not self.only_on_log:
            print(s.replace('\r', '\n'), end='', flush=True)

    def _actually_close(self):
        logger.debug("%s: 'close' called; ignoring", self)

    def __repr__(self):
        if self.only_on_log:
            return f'[output;f=log,terminal]'
        else:
            return f'[output;f=log]'
