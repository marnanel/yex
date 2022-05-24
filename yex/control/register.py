"""
Register controls.

These controls define values for registers. The registers themselves
live in yex.register.
"""
import logging
from yex.control.control import *
import yex.parse
import yex.exception

logger = logging.getLogger('yex.general')

# TODO this is in need of some refactoring.

class C_Defined_by_chardef(C_Unexpandable):

    in_vertical = 'horizontal'

    def __init__(self, char, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.char = char

    def __call__(self, tokens):
        tokens.push(
                yex.parse.get_token(
                    ch = self.char,
                ))

    def __repr__(self):
        return "[chardef: %d]" % (ord(self.char),)

    def __int__(self):
        return ord(self.char)

    @property
    def value(self):
        return self.char

class Chardef(C_Expandable):

    def __call__(self, tokens):

        newname = tokens.next(level='reading')

        if newname.category != newname.CONTROL:
            raise yex.exception.ParseError(
                    f"{name} must be followed by a control, not {token}")

        # XXX do we really want to allow them to redefine
        # XXX *any* control?

        tokens.eat_optional_equals()

        self.redefine_symbol(
                symbol = newname,
                tokens = tokens,
                )

    def redefine_symbol(self, symbol, tokens):

        char = chr(yex.value.Number(tokens).value)

        logger.debug(r"%s sets %s to %s",
                self,
                symbol,
                char)

        tokens.doc[symbol.identifier] = C_Defined_by_chardef(
                char = char)

class Mathchardef(Chardef):

    def redefine_symbol(self, symbol, tokens):
        mathchar = chr(yex.value.Number(tokens).value)

        # TODO there's nothing useful to do with this
        # until we implement math mode!

class _Registerdef(C_Expandable):

    def __call__(self, tokens):

        logger.debug(r"%s: off we go, redefining a symbol...",
                self,
                )

        newname = tokens.next(
                level='deep',
                )

        logger.debug(r"%s: the name will be %s",
                self,
                newname,
                )

        if newname.category != newname.CONTROL:
            raise yex.exception.ParseError(
                    f"{name} must be followed by a control, not {newname}")

        tokens.eat_optional_equals()

        index = r'\%s%d' % (
                self.block,
                yex.value.Number(tokens).value,
                )

        logger.debug(r"%s: the index of %s will be %s",
                self,
                newname,
                index,
                )

        existing = tokens.doc.get(
                field = index,
                )

        logger.debug(r"%s: so we set %s to %s",
                self,
                newname.identifier,
                existing,
                )

        tokens.doc[newname.identifier] = existing

class Countdef(_Registerdef):
    block = 'count'

class Dimendef(_Registerdef):
    block = 'dimen'

class Skipdef(_Registerdef):
    block = 'skip'

class Muskipdef(_Registerdef):
    block = 'muskip'

class Toksdef(_Registerdef):
    block = 'toks'

# there is no Boxdef-- see the TeXbook, p121
