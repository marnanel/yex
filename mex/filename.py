import logging

macro_logger = logging.getLogger('mex.macros')

class Filename:

    def __init__(self, tokens):

        self.tokens = tokens
        self.value = ''

        self.tokens.eat_optional_spaces()

        for c in self.tokens:
            if c.category in (c.LETTER, c.OTHER):
                macro_logger.debug("filename character: %s",
                        c)
                self.value += c.ch
            else:
                tokens.push(c)
                break

        if self.value=='':
            raise ValueError("no filename found")

        macro_logger.info("Filename is: %s", self.value)

