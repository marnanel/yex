import logging
from mex.control.word import *
import mex.exception
import mex.filename

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')
general_logger = logging.getLogger('mex.general')

class The(C_Unexpandable):

    """
    Takes an argument, one of many kinds (see the TeXbook p212ff)
    and returns a representation of that argument.

    For example, \\the\\count100 returns a series of character
    tokens representing the contents of count100.
    """

    def __call__(self, name, tokens):
        subject = tokens.next(
                expand=False,
                on_eof=tokens.EOF_RAISE_EXCEPTION,
                )

        handler = tokens.state.get(subject.name,
                default=None,
                tokens=tokens)

        try:
            method = handler.get_the
        except AttributeError:
            raise mex.exception.MexError(
                    fr"\the found no answer for {subject}")

        representation = method(
                    handler,
                    tokens)
        macros_logger.debug(r'\the for %s is %s',
                handler, representation)

        tokens.push(representation,
                clean_char_tokens=True)

class Let(C_Expandable):
    """
    TODO
    """ # TODO

    def __call__(self, name, tokens):

        lhs = tokens.next(
                expand=False,
                on_eof=tokens.EOF_RAISE_EXCEPTION,
                )

        if lhs.category!=lhs.CONTROL:
            raise mex.exception.MacroError(
                    r"\let must be followed by a token "
                    f"(and not {lhs})"
                    )

        tokens.eat_optional_equals()

        rhs = tokens.next(
                expand=True,
                on_eof=tokens.EOF_RAISE_EXCEPTION,
                )

        if rhs.category==rhs.CONTROL:
            self.redefine_to_control(lhs, rhs, tokens)
        else:
            self.redefine_to_ordinary_token(lhs, rhs, tokens)

    def redefine_to_control(self, lhs, rhs, tokens):

        rhs_referent = tokens.state.get(rhs.name,
                        default=None,
                        tokens=tokens)

        if rhs_referent is None:
            raise mex.exception.MacroError(
                    rf"\let {lhs}={rhs}, but there is no such control")

        macros_logger.debug(r"\let %s = %s, which is %s",
                lhs, rhs, rhs_referent)

        tokens.state[lhs.name] = rhs_referent

    def redefine_to_ordinary_token(self, lhs, rhs, tokens):

        class Redefined_by_let(C_Defined):

            def __call__(self, name, tokens):
                tokens.push(rhs)

            def __repr__(self):
                return f"[{rhs}]"

            @property
            def value(self):
                return rhs

        macros_logger.debug(r"\let %s = %s",
                lhs, rhs)

        tokens.state[lhs.name] = Redefined_by_let()

class Relax(C_Expandable):
    """
    Does nothing.

    See the TeXbook, p275.
    """
    def __call__(self, name, tokens):
        pass

##############################

class Noindent(C_Expandable):
    def __call__(self, name, tokens):
        if tokens.state.mode.is_vertical:
            tokens.state['_mode'] = 'horizontal'
            self.maybe_add_indent(tokens.state.mode)

    def maybe_add_indent(self, mode):
        pass # no, not here

class Indent(Noindent):

    def maybe_add_indent(self, mode):
        pass # TODO

##############################

class Noexpand(C_Unexpandable):
    def __call__(self, name, tokens):

        for t in tokens:
            return [t]

##############################

class Showlists(C_Expandable):
    def __call__(self, name, tokens):
        tokens.state.showlists()

##############################

class String(C_Unexpandable):

    def __call__(self, name, tokens,
            expand = True):

        result = []

        for t in tokens.single_shot(expand=False):

            if expand:
                token_name = '\\' + t.name
                general_logger.debug(
                        f"{name}: got token {t}")

                for token_char in token_name:
                    result.append(
                            mex.parse.token.Token(
                                ch = token_char,
                                category = 12,
                                )
                            )
            else:
                general_logger.debug(
                        f"{name}: passing token {t}")

                result.append(t)

        tokens.push(result)

##############################

class C_Upper_or_Lowercase(C_Expandable):

    def __call__(self, name, tokens,
            expand = True):

        result = []

        for token in tokens.single_shot(expand=False):
            if token.category==token.CONTROL:
                macros_logger.debug(f"{name.name}: %s is a control token",
                        token)
                result.append(token)
                continue

            replacement_code = tokens.state['%s%d' % (
                self.prefix,
                ord(token.ch))].value

            if replacement_code:
                replacement = mex.parse.Token(
                        ch = chr(replacement_code),
                        category = token.category,
                        )
            else:
                replacement = token

            macros_logger.debug(f"{name.name}: %s -> %s",
                    token, replacement)
            result.append(replacement)

        for token in reversed(result):
            tokens.push(token)

class Uppercase(C_Upper_or_Lowercase):
    prefix = 'uccode'

class Lowercase(C_Upper_or_Lowercase):
    prefix = 'lccode'

class Parshape(C_Expandable):

    def __call__(self, name, tokens):

        count = mex.value.Number(tokens).value

        if count==0:
            tokens.state.parshape = None
            return
        elif count<0:
            raise mex.exception.MexError(
                    rf"\parshape count must be >=0, not {count}"
                    )

        tokens.state.parshape = []

        for i in range(count):
            length = mex.value.Dimen(tokens)
            indent = mex.value.Dimen(tokens)
            tokens.state.parshape.append(
                    (length, indent),
                    )
            macros_logger.debug("%s: %s/%s = (%s,%s)",
                    name, i+1, count, length, indent)

    def get_the(self, name, tokens):
        if tokens.state.parshape is None:
            result = 0
        else:
            result = len(tokens.state.parshape)

        return str(result)
