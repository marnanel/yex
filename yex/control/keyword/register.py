"""
Register controls.

These controls define values for registers. The registers themselves
live in yex.control.array. (The two should probably be merged.)
"""
import logging
from yex.control import (
        Unexpandable, Expandable, Defined_by_chardef, Registerdef,
        )
import yex

logger = logging.getLogger('yex.general')

# TODO this is in need of some refactoring.

class Chardef(Expandable):

    def __call__(self, tokens):

        newname = tokens.next(level='reading')

        if newname.category != newname.CONTROL:
            raise yex.exception.ParseError(
                    f"{name} must be followed by a control, not {token}")

        # XXX do we really want to allow them to redefine
        # XXX *any* control?

        tokens.eat_optional_char('=')

        self.redefine_symbol(
                symbol = newname,
                tokens = tokens,
                )

    def redefine_symbol(self, symbol, tokens):

        char = chr(yex.value.Number.from_tokens(tokens).value)

        logger.debug(r"%s sets %s to %s",
                self,
                symbol,
                char)

        tokens.doc[symbol.identifier] = Defined_by_chardef(
                char = char)

class Mathchardef(Chardef):

    def redefine_symbol(self, symbol, tokens):
        char = chr(yex.value.Number.from_tokens(tokens).value)

        # TODO there's nothing useful to do with this
        # until we implement math mode!

        tokens.doc[symbol.identifier] = Defined_by_chardef(
                char = char)

class Countdef(Registerdef):
    block = r'\count'

class Dimendef(Registerdef):
    block = r'\dimen'

class Skipdef(Registerdef):
    block = r'\skip'

class Muskipdef(Registerdef):
    block = r'\muskip'

class Toksdef(Registerdef):
    block = r'\toks'

# there is no Boxdef-- see the TeXbook, p121
