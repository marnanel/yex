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

def conditional(control):

    def call(self, tokens):
        logger.debug(
                r"%s: before call, ifdepth=%s",
                self,
                tokens.doc.ifdepth,
                )

        whether = self._do_test(tokens)

        if whether is None:
            pass
        elif whether:
            tokens.doc.ifdepth.append(tokens.doc.ifdepth[-1])
        else:
            tokens.doc.ifdepth.append(False)

        logger.debug(
                r"%s: after call, ifdepth=%s",
                self,
                tokens.doc.ifdepth,
                )

        return None

    result = yex.decorator.control(
            expandable = True,
            conditional = True,
            push_result = False,
            )(control)
    result._do_test = result.__call__
    result.__call__ = call

    return result

@conditional
def Iftrue():
    return True

@conditional
def Iffalse():
    return False

def _ifnum_or_ifdim(tokens, our_type):

    if not tokens.doc.ifdepth[-1]:
        logger.debug(
            "  -- not reading args, because we're "
            "in a negative conditional")
        return False

    left = our_type.from_tokens(tokens)
    logger.debug("  -- left: %s", left)

    op = tokens.next()
    if op.category!=12 or not op.ch in '<=>':
        raise yex.exception.ParseError(
                "comparison operator must be <, =, or >"
                f" (not {op})")
    logger.debug("  -- op: %s", op.ch)

    right = our_type.from_tokens(tokens)
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

    return result

@conditional
def Ifnum(tokens):
    return _ifnum_or_ifdim(tokens=tokens, our_type=yex.value.Number)

@conditional
def Ifdim(tokens):
    return _ifnum_or_ifdim(tokens=tokens, our_type=yex.value.Dimen)

@conditional
def Ifodd(tokens):
    number = yex.value.Number.from_tokens(tokens)
    return int(number)%2==1

@conditional
def Ifvmode(tokens):
    return tokens.doc.mode.is_vertical

@conditional
def Ifhmode(tokens):
    return tokens.doc.mode.is_horizontal

@conditional
def Ifmmode(tokens):
    return tokens.doc.mode.is_math

@conditional
def Ifinner(tokens):
    return tokens.doc.mode.is_inner

@conditional
def If(tokens):
    left  = tokens.next(no_outer=True, level='expanding')
    right = tokens.next(no_outer=True, level='expanding')
    return left.ch==right.ch

@conditional
def Ifcat(tokens):
    left  = tokens.next(no_outer=True, level='expanding')
    right = tokens.next(no_outer=True, level='expanding')
    return left.category==right.category

@conditional
def Ifx(tokens):
    left  = tokens.next(no_outer=True, level='expanding')
    right = tokens.next(no_outer=True, level='expanding')
    logger.debug(r'\ifx: left=%s, right=%s', left, right)

    if isinstance(left, yex.parse.Token) and \
            isinstance(right, yex.parse.Token):
        logger.debug(r'\ifx: -- these are both Tokens')
        return left.ch==right.ch and left.category==right.category

    logger.debug(r'\ifx: -- these are disparate')
    return False

@conditional
def Fi(tokens):
    doc = tokens.doc

    if len(doc.ifdepth)<2:
        raise yex.exception.YexError(
                r"can't \fi; we're not in a conditional block")

    if doc.ifdepth[:-2]==[True, False]:
        logger.debug("  -- conditional block ended; resuming")

    doc.ifdepth.pop()

@conditional
def Else(tokens):
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

@conditional
def Ifcase(tokens):
    doc = tokens.doc

    logger.debug(r"\ifcase: looking for number")
    number = int(yex.value.Number.from_tokens(tokens))
    logger.debug(r"\ifcase: number is %s", number)

    case = _Case(
            number = number,
            )
    doc.ifdepth.append(case)

    logger.debug(r"\ifcase: %s", case)

    if number!=0:
        logger.debug(r"\ifcase on %d; skipping",
                number)

@conditional
def Or(tokens):
    try:
        tokens.doc.ifdepth[-1].next_case()
    except AttributeError:
        raise yex.exception.YexError(
                r"can't \or; we're not in an \ifcase block")

@conditional
def Ifeof(tokens):
    raise NotImplementedError()

@conditional
def Ifhbox(tokens):
    raise NotImplementedError()

@conditional
def Ifvbox(tokens):
    raise NotImplementedError()

@conditional
def Ifvoid(tokens):
    raise NotImplementedError()
