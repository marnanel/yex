"""
Miscellaneous macros.

These should find a home somewhere else. But for now, they live here.
"""
import logging
from yex.control.control import *
import yex.exception
import yex.filename
import yex.value
import yex.output
import yex.box
import yex.parse

logger = logging.getLogger('yex.general')

class The(C_Unexpandable):
    r"""
    Takes an argument, one of many kinds (see the TeXbook p212ff)
    and returns a representation of that argument.

    For example, \the\count100 returns a series of character
    tokens representing the contents of count100.
    """

    def __call__(self, tokens):
        subject = tokens.next(
                level='reading',
                on_eof='raise',
                )

        if isinstance(subject, yex.parse.Token):
            handler = tokens.doc.get(subject.identifier,
                    default=None,
                    tokens=tokens)

            if handler is None:
                raise yex.exception.YexError(
                        fr"\the cannot define {subject} "
                        "because it doesn't exist"
                        )
        else:
            handler = subject

        try:
            method = handler.get_the
        except AttributeError:
            raise yex.exception.YexError(
                    fr"\the found no answer for {subject}")

        representation = method(tokens)
        logger.debug(r'\the for %s is %s',
                subject, representation)

        tokens.push(representation,
                clean_char_tokens=True)

class Show(C_Unexpandable): pass
class Showthe(C_Unexpandable): pass

class Let(C_Unexpandable):
    """
    TODO
    """ # TODO

    def __call__(self, tokens):

        lhs = tokens.next(
                level='deep',
                on_eof='raise',
                )

        if not isinstance(lhs, yex.parse.Control):
            raise yex.exception.MacroError(
                    r"\let must be followed by a token "
                    f"(and not {lhs})"
                    )

        tokens.eat_optional_equals()

        rhs = tokens.next(
                level='deep',
                on_eof='raise',
                )

        if isinstance(rhs, yex.parse.Control):
            self.redefine_to_control(lhs, rhs, tokens)
        else:
            self.redefine_to_ordinary_token(lhs, rhs, tokens)

    def redefine_to_control(self, lhs, rhs, tokens):

        rhs_referent = tokens.doc.get(rhs.identifier,
                        default=None,
                        tokens=tokens)

        logger.debug(r"\let %s = %s, which is %s",
                lhs, rhs, rhs_referent)

        tokens.doc[lhs.identifier] = rhs_referent

    def redefine_to_ordinary_token(self, lhs, rhs, tokens):

        class Redefined_by_let(C_Expandable):

            def __call__(self, tokens):
                tokens.push(rhs)

            def __repr__(self):
                return f"[{rhs}]"

            @property
            def value(self):
                return rhs

        logger.debug(r"\let %s = %s",
                lhs, rhs)

        tokens.doc[lhs.identifier] = Redefined_by_let()

class Futurelet(C_Unexpandable): pass

##############################

class Meaning(C_Unexpandable): pass

##############################

class Relax(C_Unexpandable):
    """
    Does nothing.

    See the TeXbook, p275.
    """
    def __call__(self, tokens):
        pass

##############################

class Noindent(C_Unexpandable):

    vertical = 'horizontal'
    horizontal = True
    math = True

    def __call__(self, tokens):
        self.maybe_add_indent(tokens.doc.mode)

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

    def __call__(self, tokens):
        pass
##############################

class Showlists(C_Expandable):
    def __call__(self, tokens):
        tokens.doc.showlists()

##############################

class String(C_Unexpandable):

    def __call__(self, tokens,
            expand = True):

        result = []

        for t in tokens.single_shot(level='reading'):

            if expand:
                logger.debug(
                        "%s: got token %s",
                        self, t)

                for token_char in t.identifier:
                    result.append(
                            yex.parse.Other(
                                ch = token_char,
                                )
                            )
            else:
                logger.debug(
                        "%s: passing token %s",
                        self, t)

                result.append(t)

        tokens.push(result)

##############################

class C_Upper_or_Lowercase(C_Expandable):

    def __call__(self, tokens,
            expand = True):

        result = []

        for token in tokens.single_shot(level='reading'):
            if not isinstance(token, yex.parse.Token):
                logger.debug("%s: %s is not a token",
                        self, token)
                result.append(token)
                continue
            elif isinstance(token, yex.parse.Control):
                logger.debug("%s: %s is a control token",
                        self, token)
                result.append(token)
                continue

            replacement_code = tokens.doc[r'\%s%d' % (
                self.prefix,
                ord(token.ch))].value

            if replacement_code:
                replacement = yex.parse.get_token(
                        ch = chr(replacement_code),
                        category = token.category,
                        )
            else:
                replacement = token

            logger.debug("%s: %s -> %s",
                    self, token, replacement)
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

    def __call__(self, tokens):

        count = yex.value.Number(tokens).value

        if count==0:
            tokens.doc.parshape = None
            return
        elif count<0:
            raise yex.exception.YexError(
                    rf"\parshape count must be >=0, not {count}"
                    )

        tokens.doc.parshape = []

        for i in range(count):
            length = yex.value.Dimen(tokens)
            indent = yex.value.Dimen(tokens)
            tokens.doc.parshape.append(
                    (length, indent),
                    )
            logger.debug("%s: %s/%s = (%s,%s)",
                    self, i+1, count, length, indent)

    def get_the(self, tokens):
        if tokens.doc.parshape is None:
            result = 0
        else:
            result = len(tokens.doc.parshape)

        return str(result)

##############################

class S_0020(C_Unexpandable): # Space
    """
    Add an unbreakable space.
    """
    vertical = False
    horizontal = True
    math = False

    def __call__(self, tokens):
        tokens.push(
            yex.parse.token.Other(ch=chr(32)),
            )

class Par(C_Unexpandable):
    """
    Add a paragraph break.
    """
    vertical = False
    horizontal = None
    math = False

    def __call__(self, tokens):
        tokens.push(
            yex.parse.token.Paragraph(),
            )

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

class Accent(C_Unexpandable):
    vertical = False
    horizontal = True
    math = False

class Discretionary(C_Unexpandable):
    "Adds a discretionary break."
    vertical = False
    horizontal = True
    math = False

    def _read_arg(self, tokens):
        hopefully_open_brace = tokens.next(
                level='deep',
                on_eof='raise',
                )

        # It would be more elegant to modify Expander so that
        # single=True could be made to work only on a bracketed group.
        # But that would risk so many knock-on errors that it's not
        # worth it. So, we do it this way instead.

        if not isinstance(hopefully_open_brace, yex.parse.BeginningGroup):
            raise yex.exception.YexError(
                    "Needed a group between braces here")

        tokens.push(hopefully_open_brace)

        result = list(tokens.another(
            level='reading',
            on_eof='exhaust',
            single=True,
            ))

        return result

    def __call__(self, tokens):
        prebreak = self._read_arg(tokens)
        postbreak = self._read_arg(tokens)
        nobreak = self._read_arg(tokens)

        tokens.push(
            yex.box.DiscretionaryBreak(
                prebreak = prebreak,
                postbreak = postbreak,
                nobreak = nobreak,
                ),
            )

class S_002d(C_Unexpandable): # Hyphen
    vertical = False
    horizontal = True
    math = True

class Afterassignment(C_Unexpandable): pass
class Aftergroup(C_Unexpandable): pass

class Penalty(C_Unexpandable):
    def __call__(self, tokens):
        demerits = yex.value.Number(
                tokens.not_expanding()).value

        penalty = yex.box.Penalty(
                demerits = demerits,
                )

        tokens.push(penalty)

class Insert(C_Unexpandable): pass
class Vadjust(C_Unexpandable): pass

class Char(C_Unexpandable):
    def __call__(self, tokens):
        codepoint = yex.value.Number(
                tokens.not_expanding()).value

        if codepoint in range(32, 127):
            logger.debug(r"\char produces ascii %s (%s)",
                codepoint, chr(codepoint))
        else:
            logger.debug(r"\char produces ascii %s",
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

class End(C_Unexpandable):
    horizontal = 'vertical'
    vertical = True

class Shipout(C_Unexpandable):
    r'''Sends a box to the output.

    "You can say \shipout anywhere" -- TeXbook, p252'''

    horizontal = True
    vertical = True
    math = True

    def __call__(self, tokens):

        found = tokens.next(level='querying')
        try:
            boxes = found.value
        except AttributeError:
            boxes = [found]

        for box in boxes:
            logger.debug(r'%s: shipping %s',
                    self, box)

            if not isinstance(box, yex.box.Gismo):
                raise yex.exception.YexError(
                        f"needed a box or similar here, not {box}",
                        )

            tokens.doc.shipout(box)

class Expandafter(C_Unexpandable): pass
class Ignorespaces(C_Unexpandable): pass

##############################

class Number(C_Unexpandable): pass
class Romannumeral(Number): pass
