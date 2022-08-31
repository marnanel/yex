import os
import yex
import logging

logger = logging.getLogger('yex.general')

class StreamsTable:
    def __init__(self):
        self._inputs = {}
        self._outputs = {}

    def openin(self, number, filetokens):
        try:
            with open(filename, 'r') as f:
                result = InputStream(f=f, tokens=tokens)
                self._inputs[number] = result
                return result
        except OEError as ose:
            logger.info(fr"\openin{number}={filename} failed: {ose}")

    def openout(self, number, filename):
        try:
            with open(filename, 'w') as f:
                result = OutputStream(f=f)
                self._outputs[number] = result
                return result
        except OEError as ose:
            logger.info(fr"\openout{number}={filename} failed: {ose}")

class InputStream:
    """
    A stream for input.

    Most of this behaviour is specified on p215 of the TeXbook.
    """

    def __init__(self, doc, filename):
        self.doc = doc
        self.brackets_balance = 0

        filename = _maybe_add_tex_extension(filename)

        try:
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
        if self.f is None:
            return '[input;closed]'
        else:
            return f'[input;f={self.f}]'

    def close(self):
        logger.debug("%s: closing", self)
        if self.f is not None:
            self.f.close()
            self.f = None
        self.eof = True

class TerminalInputStream(InputStream):

    def __init__(self,
            doc,
            show_variable_names,
            ):

        self.doc = doc
        self.show_variable_names = show_variable_names
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
        return f'[input;f=terminal;show={self.show_variable_names}]'

class OutputStream:

    def __init__(self, filename):

        filename = _maybe_add_tex_extension(filename)
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
        if self.f is None:
            return '[output;closed]'
        else:
            return f'[output;f={self.f}]'

class TerminalOutput:
    def write(self, s):
        print(s.replace('\r', '\n'), end='', flush=True)

    def __repr__(self):
        return f'[output;f=terminal]'

def _maybe_add_tex_extension(filename):
    _, ext = os.path.splitext(filename)
    if not ext:
        filename += os.extsep + 'tex'
    return filename
