"""
Condition controls.

These controls affect the flow of control. They are all expandable.
"""
import yex.logging
from yex.decorator import control as yex_decorator_control
import yex.parse
import yex.value
import yex.exception
from typing import Type, Union

logger = yex.logging.getLogger('control')

def conditional(
        control: 'yex.control.Control',
        ) -> None:
    r"""
    Decorator: turns a function into an Unexpandable affecting control flow.

    If the function returns `True` or `False`, we push a value to the doc.ifdepth
    stack, and notify `\tracingcommands`. If the previous topmost value in
    the ifdepth stack equalled True, we push the value the function returned
    (since if you're executing and you see an `\if`, it turns execution
    on or off). If the previous topmost value equalled `False`, we push
    another False (since if you're not executing, an `\if` can't turn
    execution on).

    If the function returns None, we do nothing here; you'll have to handle
    modifying the ifdepth stack and logging yourself.
    """

    def call(self,
             tokens: yex.parse.Expander) -> Union[bool, None]:
        logger.debug(
                r"%s: before call, ifdepth=%s",
                self,
                tokens.doc.ifdepth,
                )

        def _tracingcommands_log(message):
            self.doc.tracingcommands.notice_conditional(
                    '\\' + self.__class__.__name__.lower(),
                    )
            self.doc.tracingcommands.notice_conditional(
                    message,
                    )

        whether = self._do_test(tokens)

        assert whether in [None, True, False]

        if whether is None:
            pass
        elif whether:
            _tracingcommands_log('true')
            tokens.doc.ifdepth.append(tokens.doc.ifdepth[-1])
        else:
            _tracingcommands_log('false')
            tokens.doc.ifdepth.append(False)

        logger.debug(
                r"%s: after call, ifdepth=%s",
                self,
                tokens.doc.ifdepth,
                )

        return None # don't push any tokens

    result = yex_decorator_control(
            expandable = True,
            conditional = True,
            push_result = False,
            )(control)
    result._do_test = result.__call__
    result.__call__ = call

    return result

@conditional
def Iftrue() -> bool:
    return True

@conditional
def Iffalse() -> bool:
    return False

def _ifnum_or_ifdim(
        tokens: yex.parse.Expander,
        our_type: Type,
        ) -> bool:

    if not tokens.doc.ifdepth[-1]:
        logger.debug(
            "  -- not reading args, because we're "
            "in a negative conditional")
        return False

    left = our_type.from_tokens(tokens)
    logger.debug("  -- left: %s", left)

    op = tokens.next()
    if op.category!=12 or not op.ch in '<=>':
        raise WeirdComparisonOperator(
                problem = op,
                )
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
def Ifnum(
        tokens: yex.parse.Expander,
        ) -> bool:
    return _ifnum_or_ifdim(
            tokens=tokens, our_type=yex.value.Number)

@conditional
def Ifdim(
        tokens: yex.parse.Expander,
        ) -> bool:
    return _ifnum_or_ifdim(
            tokens=tokens, our_type=yex.value.Dimen)

@conditional
def Ifodd(
        tokens: yex.parse.Expander,
        ) -> bool:
    number = yex.value.Number.from_tokens(tokens)
    return int(number)%2==1

@conditional
def Ifvmode(
        tokens: yex.parse.Expander,
        ) -> bool:
    return tokens.doc.mode.is_vertical

@conditional
def Ifhmode(
        tokens: yex.parse.Expander,
        ) -> bool:
    return tokens.doc.mode.is_horizontal

@conditional
def Ifmmode(
        tokens: yex.parse.Expander,
        ) -> bool:
    return tokens.doc.mode.is_math

@conditional
def Ifinner(
        tokens: yex.parse.Expander,
        ) -> bool:
    return tokens.doc.mode.is_inner

@conditional
def If(
        tokens: yex.parse.Expander,
        ) -> bool:
    left  = tokens.next(no_outer=True, level='expanding')
    right = tokens.next(no_outer=True, level='expanding')
    return str(left)==str(right)

@conditional
def Ifcat(
        tokens: yex.parse.Expander,
        ) -> bool:
    left  = tokens.next(no_outer=True, level='expanding')
    right = tokens.next(no_outer=True, level='expanding')
    return left.category==right.category

@conditional
def Ifx(
        tokens: yex.parse.Expander,
        ) -> bool:
    left  = tokens.next(level='deep')
    right = tokens.next(level='deep')

    def maybe_deref(c) -> bool:
        if isinstance(c, (yex.parse.Control, yex.parse.Active)):
            c = tokens.doc.get(c.identifier,
                    default = c,
                    param_control = True,
                    )

        return c

    left = maybe_deref(left)
    right = maybe_deref(right)

    logger.debug(r'\ifx: left=%s, right=%s', left, right)

    if (not isinstance(left, right.__class__)) and \
            (not isinstance(right, left.__class__)):
                logger.debug(r'\ifx: -- these are disparate')
                return False

    # henceforth we know that left and right are of the same type

    if isinstance(left, yex.parse.Token):

        logger.debug(r'\ifx: -- these are tokens, so undefined')
        return True # TeX says all undefined control words compare equal

    elif isinstance(left, yex.control.Register):

        logger.debug(r'\ifx: -- these are registers')
        return left.parent==right.parent and left.index==right.index

    elif isinstance(left, yex.control.Macro):

        left_serialised  = left.__getstate__()
        right_serialised = right.__getstate__()

        logger.debug(r'\ifx: -- these are macros: %s vs %s',
                left_serialised, right_serialised)

        for comparand in ['flags', 'definition']:
            if left_serialised.get(comparand, None) != \
                    right_serialised.get(comparand, None):
                        return False

        return True

    try:
        logger.debug(r'\ifx: -- idk about %s; fallback to its __eq__',
                type(left))
        return left==right
    except TypeError as te:
        logger.debug(r'\ifx:   -- %s; returning False', te)
        return False

@conditional
def Fi(
        tokens: yex.parse.Expander,
        ) -> bool:
    doc = tokens.doc

    if len(doc.ifdepth)<2:
        raise yex.exception.FiNotInConditionalBlockError()

    if doc.ifdepth[:-2]==[True, False]:
        logger.debug("  -- conditional block ended; resuming")

    finished_true = doc.ifdepth.pop()

    if finished_true:
        doc.tracingcommands.notice_conditional(r'\fi')

@conditional
def Else(
        tokens: yex.parse.Expander,
        ) -> bool:
    doc = tokens.doc

    if len(doc.ifdepth)<2:
        raise yex.exception.ElseNotInConditionalBlockError()

    if not doc.ifdepth[-2]:
        # \else can't turn on execution unless we were already executing
        # before this conditional block
        return None

    try:
        return tokens.doc.ifdepth[-1].else_case()
    except AttributeError:
        doc.tracingcommands.notice_conditional(r'\else')
        return not doc.ifdepth.pop()

class _Case:
    r"""
    Counts the \ors in a \case block.

    Most of the values in doc.ifdepth are ordinary Python bools.
    Instances of *this* class, however, also live in doc.ifdepth.
    They evaluate to True or False depending on how many \ors we
    have seen in the current \case block.

    Fields:
        number (int): how many \ors we're looking for
        count (int): how many \ors we've seen
        constant (bool or None): if this is non-None, we only
            evaluate to this value. If it's None, we're counting
            \ors as usual. This is used internally to turn ourselves
            off when we see another \or ending our own part.
        doc (Document or None): if not None, we use this to report
            back to \tracingcommands.
    """
    def __init__(self, number, doc=None):
        self.number = number
        self.count = 0
        self.constant = None
        self.doc = doc

    def __bool__(self):
        if self.constant is not None:
            return self.constant

        return self.number==self.count

    def next_case(self) -> None:
        logger.debug(r"\or: %s", self)

        if self.number==self.count:
            logger.debug(r"\or: skipping")

            if self.constant is None:
                self.constant = False
                if self.doc is not None:
                    self.doc.tracingcommands.notice_conditional(fr'\or')

            return

        self.count += 1

        if self.number==self.count:
            logger.debug(r"\or: resuming")

    def else_case(self) -> None:
        if self.constant==False:
            return
        elif self.number==self.count:
            if self.doc is not None:
                self.doc.tracingcommands.notice_conditional(fr'\else')

            self.constant = False
            return

        logger.debug(r"\else: resuming")
        self.constant = True

    def __repr__(self):
        if self.constant is not None:
            return f'({self.constant})'

        return f'{self.count}/{self.number}'

@conditional
def Ifcase(
        tokens: yex.parse.Expander,
        ) -> None:
    doc = tokens.doc

    logger.debug(r"\ifcase: looking for number")
    number = int(yex.value.Number.from_tokens(tokens))
    logger.debug(r"\ifcase: number is %s", number)

    doc.tracingcommands.notice_conditional(fr'\ifcase')
    doc.tracingcommands.notice_conditional(f'case {number}')

    case = _Case(
            number = number,
            doc = doc,
            )
    doc.ifdepth.append(case)

    logger.debug(r"\ifcase: %s", case)

    if number!=0:
        logger.debug(r"\ifcase on %d; skipping",
                number)

    return None

@conditional
def Or(
        tokens: yex.parse.Expander,
       ) -> None:
    try:
        tokens.doc.ifdepth[-1].next_case()
    except AttributeError:
        raise yex.exception.OrNotInCaseBlockError()

    return None

@conditional
def Ifeof(
        stream_id: int,
        tokens: yex.parse.Expander,
        ) -> bool:
    stream = tokens.doc[f'_inputs;{stream_id}']
    logger.debug(r'\ifeof: stream is %s; eof is %s', stream, stream.eof)

    return stream.eof

@conditional
def Ifhbox(
        box: int,
        tokens: yex.parse.Expander,
        ) -> bool:
    return isinstance(tokens.doc[fr'\copy{box}'], yex.box.HBox)

@conditional
def Ifvbox(
        box: int,
        tokens: yex.parse.Expander,
        ) -> bool:
    return isinstance(tokens.doc[fr'\copy{box}'], yex.box.VBox)

@conditional
def Ifvoid(
        box: int,
        tokens: yex.parse.Expander,
        ) -> bool:
    return tokens.doc[fr'\copy{box}'].is_void()
