import logging
from mex.control.word import *
import mex.exception
import mex.filename
import mex.value

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
                subject, representation)

        tokens.push(representation,
                clean_char_tokens=True)

class Show(C_Unexpandable): pass
class Showthe(C_Unexpandable): pass

class Let(C_Unexpandable):
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
                expand=False,
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

class Futurelet(C_Unexpandable): pass

##############################

class Meaning(C_Unexpandable): pass

##############################

class Relax(C_Unexpandable):
    """
    Does nothing.

    See the TeXbook, p275.
    """
    def __call__(self, name, tokens):
        pass

##############################

class Noindent(C_Unexpandable):

    vertical = 'horizontal'
    horizontal = True
    math = True

    def __call__(self, name, tokens):
        self.maybe_add_indent(tokens.state.mode)

    def maybe_add_indent(self, mode):
        pass # no, not here

class Indent(Noindent):

    def maybe_add_indent(self, mode):
        pass # TODO

##############################

class C_Begin_or_end_group(C_Expandable):
    pass

class Begingroup(C_Begin_or_end_group): pass
class Endgroup(C_Begin_or_end_group): pass

##############################

class Noexpand(C_Expandable):
    """
    The argument is not expanded.

    This is special-cased in Expander. After it calls us,
    it pops the stack and returns the contents.
    """

    def __call__(self, name, tokens):
        pass
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

##############################

class Csname(C_Unexpandable):
    pass
class Endcsname(C_Unexpandable):
    pass

##############################

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

class Par(C_Unexpandable):
    vertical = False
    horizontal = None
    math = False

    def __call__(self, name, tokens):
        pass

##############################

class Noboundary(C_Unexpandable):
    vertical = False
    horizontal = True
    math = False

class Unhbox(C_Unexpandable):
    vertical = False
    horizontal = True
    math = True

class Unhcopy(C_Unexpandable):
    vertical = False
    horizontal = True
    math = True

class Valign(C_Unexpandable):
    vertical = False
    horizontal = True
    math = False

class Vrule(C_Unexpandable):
    vertical = False
    horizontal = True
    math = False

class Hskip(C_Unexpandable):
    vertical = False
    horizontal = True
    math = True

class Hfil(C_Unexpandable):
    vertical = False
    horizontal = True
    math = True

class Hfilneg(Hfil): pass

class Hfill(Hfil):
    math = False
class Hfilll(Hfill): pass

class Hss(C_Unexpandable):
    vertical = False
    horizontal = True
    math = True

class Accent(C_Unexpandable):
    vertical = False
    horizontal = True
    math = False

class Discretionary(C_Unexpandable):
    vertical = False
    horizontal = True
    math = False

# Horizontal:
# And: \- and "\ ". AFAIK we don't have a way to initialise active characters
# yet. TODO

class Afterassignment(C_Unexpandable): pass
class Aftergroup(C_Unexpandable): pass
class Penalty(C_Unexpandable): pass
class Insert(C_Unexpandable): pass
class Vadjust(C_Unexpandable): pass

class Char(C_Unexpandable):
    def __call__(self, name, tokens):
        codepoint = mex.value.Number(
                tokens.not_expanding()).value

        if codepoint in range(32, 127):
            macros_logger.debug(r"\char produces ascii %s (%s)",
                codepoint, chr(codepoint))
        else:
            macros_logger.debug(r"\char produces ascii %s",
                codepoint)

        tokens.push(chr(codepoint))

class Unvbox(C_Unexpandable):
    horizontal = 'vertical'
    vertical = True

class Unvcopy(C_Unexpandable):
    horizontal = 'vertical'
    vertical = True

class Halign(C_Unexpandable):
    horizontal = 'vertical'
    vertical = True

class Noalign(C_Unexpandable):
    pass

class Hrule(C_Unexpandable):
    horizontal = 'vertical'
    vertical = True

class Vskip(C_Unexpandable):
    horizontal = 'vertical'
    vertical = True

class Vfil(C_Unexpandable):
    horizontal = 'vertical'
    vertical = True

class Vfilneg(Vfil): pass
class Vfill(Vfil): pass
class Vss(Vfil): pass

class End(C_Unexpandable):
    horizontal = 'vertical'
    vertical = True

class Shipout(C_Unexpandable):
    r'''Sends a box to the output.

    "You can say \shipout anywhere" -- TeXbook, p252'''

    horizontal = True
    vertical = True
    math = True

class Expandafter(C_Unexpandable): pass
class Ignorespaces(C_Unexpandable): pass

##############################

class Number(C_Unexpandable): pass
class Romannumeral(Number): pass
