"""
Condition controls.

These controls affect the flow of control. They are all expandable.
"""
import logging
from yex.control.control import *
import yex.parse
import yex.value
import yex.exception

logger = logging.getLogger('yex.general')

class C_Conditional(C_Expandable):
    """
    A command which affects the flow of control.
    """
    def __call__(self, tokens):
        """
        Executes this conditional. The actual work
        is delegated to self.do_conditional().
        """
        logger.debug(
                r"%s: before call, ifdepth=%s",
                self,
                tokens.doc.ifdepth,
                )

        self.do_conditional(tokens)

        logger.debug(
                r"%s: after call, ifdepth=%s",
                self,
                tokens.doc.ifdepth,
                )

    def do_conditional(self, tokens):
        """
        Decides whether the condition has been met, and
        what to do about it.
        """
        raise NotImplementedError()

    def _do_the_choice(self, doc, whether):
        """
        Call this from do_conditional() when you know which way to go.
        """
        if whether:
            doc.ifdepth.append(
                    doc.ifdepth[-1])
        else:
            if doc.ifdepth[-1]:
                logger.debug("  -- was false; skipping")

            doc.ifdepth.append(False)

class Iftrue(C_Conditional):
    def do_conditional(self, tokens):
        self._do_the_choice(tokens.doc, True)

class Iffalse(C_Conditional):
    def do_conditional(self, tokens):
        self._do_the_choice(tokens.doc, False)

class _Ifnum_or_Ifdim(C_Conditional):
    def do_conditional(self, tokens):

        if not tokens.doc.ifdepth[-1]:
            logger.debug(
                "  -- not reading args, because we're "
                "in a negative conditional")
            self._do_the_choice(tokens.doc, False)
            return

        left = self._get_value(tokens)
        logger.debug("  -- left: %s", left)

        op = tokens.next()
        if op.category!=12 or not op.ch in '<=>':
            raise yex.exception.ParseError(
                    "comparison operator must be <, =, or >"
                    f" (not {op})")
        logger.debug("  -- op: %s", op.ch)

        right = self._get_value(tokens)
        logger.debug("  -- right: %s", right)

        if op.ch=='<':
            result = left.value<right.value
        elif op.ch=='=':
            result = left.value==right.value
        else:
            result = left.value>right.value

        logger.debug(
                r"\ifnum %s%s%s == %s",
                    left, op.ch, right, result)

        self._do_the_choice(tokens.doc, result)

class Ifnum(_Ifnum_or_Ifdim):
    def _get_value(self, tokens):
        return yex.value.Number(tokens)

class Ifdim(_Ifnum_or_Ifdim):
    def _get_value(self, tokens):
        return yex.value.Dimen(tokens)

class Ifodd(C_Conditional):
    def do_conditional(self, tokens):

        number = yex.value.Number(tokens)

        self._do_the_choice(tokens.doc,
                whether = int(number)%2==1,
                )

class _Ifmode(C_Conditional):
    def do_conditional(self, tokens):
        current_mode = tokens.doc.mode
        whether = self.mode_matches(current_mode)
        logger.debug(
                "%s: consider %s: %s",
                self, current_mode, whether)

        self._do_the_choice(tokens.doc, whether)

class Ifvmode(_Ifmode):
    def mode_matches(self, mode):
        return mode.is_vertical

class Ifhmode(_Ifmode):
    def mode_matches(self, mode):
        return mode.is_horizontal

class Ifmmode(_Ifmode):
    def mode_matches(self, mode):
        return mode.is_math

class Ifinner(_Ifmode):
    def mode_matches(self, mode):
        return mode.is_inner

class _If_or_Ifcat(C_Conditional):
    def do_conditional(self, tokens):

        comparands = []

        left = tokens.next(
                no_outer=True,
                level='expanding',
                )
        right = tokens.next(
                no_outer=True,
                level='expanding',
                )

        logger.debug(
                r"\%s: %s, %s ",
                self.__class__.__name__.lower(),
                left, right,
                )

        self._do_the_choice(tokens.doc,
                whether = self.get_field(left)==self.get_field(right),
                )

class If(_If_or_Ifcat):
    def get_field(self, t):
        return t.ch

class Ifcat(_If_or_Ifcat):
    def get_field(self, t):
        return t.category

class Ifx(C_Conditional): pass

class Fi(C_Conditional):
    def do_conditional(self, tokens):

        doc = tokens.doc

        if len(doc.ifdepth)<2:
            raise yex.exception.YexError(
                    r"can't \fi; we're not in a conditional block")

        if doc.ifdepth[:-2]==[True, False]:
            logger.debug("  -- conditional block ended; resuming")

        doc.ifdepth.pop()

class Else(C_Conditional):

    def do_conditional(self, tokens):

        doc = tokens.doc

        if len(doc.ifdepth)<2:
            raise yex.exception.YexError(
                    r"can't \else; we're not in a conditional block")

        if not doc.ifdepth[-2]:
            # \else can't turn on execution unless we were already executing
            # before this conditional block
            return

        try:
            tokens.doc.ifdepth[-1].else_case()
        except AttributeError:
            doc.ifdepth.append(not doc.ifdepth.pop())
            if doc.ifdepth[-1]:
                logger.debug(r"\else: resuming")
            else:
                logger.debug(r"\else: skipping")

class Ifcase(C_Conditional):

    class _Case:
        def __init__(self, number):
            self.number = number
            self.count = 0
            self.constant = None

        def __bool__(self):
            if self.constant is not None:
                return self.constant

            return self.number==self.count

        def next_case(self):
            logger.debug(r"\or: %s", self)

            if self.number==self.count:
                logger.debug(r"\or: skipping")
                self.constant = False
                return

            self.count += 1

            if self.number==self.count:
                logger.debug(r"\or: resuming")

        def else_case(self):
            if self.constant==False:
                return
            elif self.number==self.count:
                self.constant = False
                return

            logger.debug(r"\else: resuming")
            self.constant = True

        def __repr__(self):
            if self.constant is not None:
                return f'({self.constant})'

            return f'{self.count}/{self.number}'

    def do_conditional(self, tokens):

        doc = tokens.doc

        logger.debug(r"\ifcase: looking for number")
        number = int(yex.value.Number(tokens))
        logger.debug(r"\ifcase: number is %s", number)

        case = self._Case(
                number = number,
                )
        doc.ifdepth.append(case)

        logger.debug(r"\ifcase: %s", case)

        if number!=0:
            logger.debug(r"\ifcase on %d; skipping",
                    number)

class Or(C_Conditional):
    def do_conditional(self, tokens):
        try:
            tokens.doc.ifdepth[-1].next_case()
        except AttributeError:
            raise yex.exception.YexError(
                    r"can't \or; we're not in an \ifcase block")

class Ifeof(C_Conditional): pass
class C_Ifbox(C_Conditional): pass
class Ifhbox(C_Ifbox): pass
class Ifvbox(C_Ifbox): pass
class Ifvoid(C_Ifbox): pass
