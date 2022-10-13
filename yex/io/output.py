import os
import yex
import logging
from yex.parse.pushback import Pushback

logger = logging.getLogger('yex.general')

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
