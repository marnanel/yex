import logging
from mex.control.word import C_ControlWord, C_Defined
import mex.exception

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')

# TODO this is in need of some refactoring.

class Chardef(C_ControlWord):

    def __call__(self, name, tokens):

        tokens.running = False
        newname = tokens.__next__()
        tokens.running = True

        if newname.category != newname.CONTROL:
            raise mex.exception.ParseError(
                    f"{name} must be followed by a control, not {token}")

        # XXX do we really want to allow them to redefine
        # XXX *any* control?

        tokens.eat_optional_equals()

        self.redefine_symbol(
                symbol = newname,
                tokens = tokens,
                )

    def redefine_symbol(self, symbol, tokens):

        char = chr(mex.value.Number(tokens).value)

        class Redefined_by_chardef(C_Defined):

            def __call__(self, name, tokens):
                return char

            def __repr__(self):
                return "[chardef: %d]" % (ord(char),)

            @property
            def value(self):
                return char

        tokens.state[symbol.name] = Redefined_by_chardef()

class Mathchardef(Chardef):

    def redefine_symbol(self, symbol, tokens):
        mathchar = chr(mex.value.Number(tokens).value)

        # TODO there's nothing useful to do with this
        # until we implement math mode!

class _Registerdef(C_ControlWord):

    def __call__(self, name, tokens):

        tokens.running = False
        newname = tokens.__next__()
        tokens.running = True

        if newname.category != newname.CONTROL:
            raise mex.exception.ParseError(
                    f"{name} must be followed by a control, not {newname}")

        tokens.eat_optional_equals()

        index = self.block + str(mex.value.Number(tokens).value)

        existing = tokens.state.get(
                field = index,
                )
        commands_logger.debug(r"%s sets \%s to %s",
                name,
                newname.name,
                existing)

        tokens.state[newname.name] = existing

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
