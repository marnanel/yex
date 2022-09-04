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
                result = self.our_type(filename=filename, doc=self.doc)
                self.streams[number] = result
                logger.debug("%s: opened %s = %s",
                        self, number, repr(filename))
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

    def __getitem__(self, number):

        if number<0 or number>15:
            logger.debug("%s: returning terminal for stream number %s",
                self, number)
            return self.our_type.on_terminal(doc=self.doc, number=number)

        if number not in self.streams:
            logger.debug(("%s: no stream %s; "
                "creating and returning empty stream"),
                self, number)

            self.streams[number] = self.our_type(
                    filename=None,
                    doc=self.doc,
                    )

        return self.streams[number]

    def __str__(self):
        return f'{self.our_type.__name__} table'

class InputStream:
    """
    A stream for input.

    Most of this behaviour is specified on p215 of the TeXbook.
    """

    def __init__(self, doc, filename):

        self.doc = doc
        self.brackets_balance = 0

        logger.debug("%s: opening %s", self, filename)

        if filename is None:
            self.f = None
            return

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

    def read(self):
        r"""
        Reads a line from the input, tokenises it, and
        returns the result. Keeps reading lines until
        the curly brackets balance.
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

        self.brackets_balance = 0

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
                    self.brackets_balance += 1
                elif isinstance(t, yex.parse.EndGroup):
                    self.brackets_balance -= 1
                    if self.brackets_balance < 0:
                        return result

                result.append(t)

            if self.brackets_balance==0:
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
            name=None):
        if self.show_variable_names and name is not None:
            print(fr'\{name}=', end='', flush=True)

        return super().read()

    def close(self):
        logger.debug("%s: 'close' called; ignoring", self)

    def __repr__(self):
        if self.show_variable_names:
            return '[input;f=terminal;show vars]'
        else:
            return '[input;f=terminal]'

class OutputStream:

    def __init__(self, filename, doc):

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

    def write(self, s):
        logger.debug("%s: writing: %s", self, repr(s))

        if self.f is None:
            logger.debug("%s: but the stream is closed", self)
            raise ValueError("the stream is closed")

        self.f.write(f"{s}\n")
        self.f.flush()

    def close(self):
        logger.debug("%s: closing", self)
        if self.f is not None:
            self.f.close()
            self.f = None

    def __repr__(self):
        try:
            if self.f is None:
                return '[output;closed]'

            return f'[output;f={repr(self.f.name)}]'
        except:
            return '[output;f=?]'

    @classmethod
    def on_terminal(cls, doc, number):
        return TerminalOutputStream(doc, number)

class TerminalOutputStream:
    def __init__(self, doc, number):
        self.only_on_log = number<0

    def write(self, s):
        for line in s.split('\r'):
            logger.info("Log: %s", line)
        if not self.only_on_log:
            print(s.replace('\r', '\n'), end='', flush=True)

    def __repr__(self):
        if self.only_on_log:
            return f'[output;f=log,terminal]'
        else:
            return f'[output;f=log]'
