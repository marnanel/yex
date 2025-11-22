"""
Register controls.

These controls define values for registers. The registers themselves
live in yex.control.array. (The two should probably be merged.)
"""
import yex.logging
from yex.control import (
        Unexpandable, Expandable, Defined_by_chardef, Registerdef,
        )
import yex

logger = yex.logging.getLogger('control')

# TODO this is in need of some refactoring.

class Chardef(Expandable):

    def __call__(self, parser):

        newname = parser.next(level='reading')

        if newname.category != newname.CONTROL:
            raise yex.exception.LetInvalidLhsError(
                    name = name,
                    subject = token,
                    )

        # XXX do we really want to allow them to redefine
        # XXX *any* control?

        parser.eat_optional_char('=')

        self.redefine_symbol(
                symbol = newname,
                parser = parser,
                )

    def redefine_symbol(self, symbol, parser):

        char = chr(yex.value.Number.from_parser(parser).value)

        logger.debug(r"%s sets %s to %s",
                self,
                symbol,
                char)

        parser.doc[symbol.identifier] = Defined_by_chardef(
                char = char)

class Mathchardef(Chardef):

    def redefine_symbol(self, symbol, parser):
        char = chr(yex.value.Number.from_parser(parser).value)

        # TODO there's nothing useful to do with this
        # until we implement math mode!

        parser.doc[symbol.identifier] = Defined_by_chardef(
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
