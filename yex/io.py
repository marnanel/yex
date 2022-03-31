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
    A stream open for input.

    Most of this behaviour is specified on p215 of the TeXbook.
    """

    def __init__(self, f=None,
            tokens = None):
        """
        f is a file-like object, open for input.

        However, if f is None, the stream will be created closed.
        """
        self.f = f
        self.tokens = tokens

    @property
    def at_eof(self):
        return self.f is None

    def read(self,
            name=None):
        r"""
        Reads a line from the input, tokenises it, and
        returns the result. Keeps reading lines until
        the curly brackets balance.

        If there are no more lines, returns None.
        But if we're constructed on a disk file,
        we return an extra empty line, per the TeXbook p215.

        "name" is the name of the macro you're about to
        create, which (depending on the format of \openin)
        might be printed on the terminal if we're reading from there.
        It can be None, in which case nothing ever gets printed.
        """

        # XXX What if the lines run out before the brackets balance?
        raise NotImplementedError()

    def __repr__(self):
        if self.f is None:
            return '[input;closed]'
        else:
            return f'[input;f={self.f}]'

class TerminalInput(InputStream):

    def __init__(self,
            show_variable_names = True,
            ):
        self.show_variable_names = show_variable_names

    def at_eof(self):
        return False

    def read(self,
            name=None):
        if self.show_variable_names and name is not None:
            print(fr'\{name}=', end='', flush=True)

        result = input() + r'\r'

    def __repr__(self):
        return f'[input;f=terminal;show={self.show_variable_names}]'

class OutputStream:

    def __init__(self, f):
        """
        f is a file-like object, open for output.
        """
        self.f = f

    def write(self, s):
        raise NotImplementedError()

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
