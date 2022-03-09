import logging
from mex.control.word import C_ControlWord
import mex.parse
import mex.value
import mex.exception

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')

class C_Conditional(C_ControlWord):
    """
    A command which affects the flow of control.
    """
    def __call__(self, name, tokens):
        """
        Executes this conditional. The actual work
        is delegated to self.do_conditional().
        """
        commands_logger.debug(
                r"%s: from %s",
                name,
                tokens.state.ifdepth,
                )

        self.do_conditional(tokens)

    def do_conditional(self, tokens):
        """
        Decides whether the condition has been met, and
        what to do about it.
        """
        raise NotImplementedError()

    def _do_true(self, state):
        """
        Convenience method for do_conditional() to call if
        the result is True.
        """
        state.ifdepth.append(
                state.ifdepth[-1])

    def _do_false(self, state):
        """
        Convenience method for do_conditional() to call if
        the result is False.
        """
        if state.ifdepth[-1]:
            commands_logger.debug("  -- was false; skipping")

        state.ifdepth.append(False)

class Iftrue(C_Conditional):
    def do_conditional(self, tokens):
        self._do_true(tokens.state)

class Iffalse(C_Conditional):
    def do_conditional(self, tokens):
        self._do_false(tokens.state)

class _Ifnum_or_Ifdim(C_Conditional):
    def do_conditional(self, tokens):

        left = self._get_value(tokens)
        macros_logger.debug("  -- left: %s", left)

        op = tokens.next()
        if op.category!=12 or not op.ch in '<=>':
            raise mex.exception.ParseError(
                    "comparison operator must be <, =, or >"
                    f" (not {op})")
        macros_logger.debug("  -- op: %s", op.ch)

        right = self._get_value(tokens)
        macros_logger.debug("  -- right: %s", right)

        if op.ch=='<':
            result = left.value<right.value
        elif op.ch=='=':
            result = left.value==right.value
        else:
            result = left.value>right.value

        commands_logger.debug(
                r"\ifnum %s%s%s == %s",
                    left, op.ch, right, result)

        if result:
            self._do_true(tokens.state)
        else:
            self._do_false(tokens.state)

class Ifnum(_Ifnum_or_Ifdim):
    def _get_value(self, tokens):
        return mex.value.Number(tokens)

class Ifdim(_Ifnum_or_Ifdim):
    def _get_value(self, tokens):
        return mex.value.Dimen(tokens)

class Ifodd(C_Conditional):
    def do_conditional(self, tokens):

        number = mex.value.Number(tokens)

        if int(number)%2==0:
            self._do_false(tokens.state)
        else:
            self._do_true(tokens.state)

class _Ifmode(C_Conditional):
    def do_conditional(self, tokens):
        whether = self.mode_matches(tokens.state.mode)

        if whether:
            self._do_true(tokens.state)
        else:
            self._do_false(tokens.state)

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

        for t in tokens.child(
                no_outer=True,
                ):
            comparands.append(t)
            if len(comparands)>1:
                break

        commands_logger.debug(
                r"\%s %s",
                self.__class__.__name__.lower(),
                comparands)

        if self.get_field(comparands[0])==\
                self.get_field(comparands[1]):
            self._do_true(tokens.state)
        else:
            self._do_false(tokens.state)

class If(_If_or_Ifcat):
    def get_field(self, t):
        return t.ch

class Ifcat(_If_or_Ifcat):
    def get_field(self, t):
        return t.category

class Fi(C_Conditional):
    def do_conditional(self, tokens):

        state = tokens.state

        if len(state.ifdepth)<2:
            raise mex.exception.MexError(
                    r"can't \fi; we're not in a conditional block")

        if state.ifdepth[:-2]==[True, False]:
            commands_logger.debug("  -- conditional block ended; resuming")

        state.ifdepth.pop()

class Else(C_Conditional):

    def do_conditional(self, tokens):

        state = tokens.state

        if len(state.ifdepth)<2:
            raise MexError(r"can't \else; we're not in a conditional block")

        if not state.ifdepth[-2]:
            # \else can't turn on execution unless we were already executing
            # before this conditional block
            return

        try:
            tokens.state.ifdepth[-1].else_case()
        except AttributeError:
            state.ifdepth.append(not state.ifdepth.pop())
            if state.ifdepth[-1]:
                commands_logger.debug(r"\else: resuming")
            else:
                commands_logger.debug(r"\else: skipping")

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
            commands_logger.debug(r"\or: %s", self)

            if self.number==self.count:
                commands_logger.debug(r"\or: skipping")
                self.constant = False
                return

            self.count += 1

            if self.number==self.count:
                commands_logger.debug(r"\or: resuming")

        def else_case(self):
            if self.constant==False:
                return
            elif self.number==self.count:
                self.constant = False
                return

            commands_logger.debug(r"\else: resuming")
            self.constant = True

        def __repr__(self):
            if self.constant is not None:
                return f'({self.constant})'

            return f'{self.count}/{self.number}'

    def do_conditional(self, tokens):

        state = tokens.state

        number = int(mex.value.Number(tokens))

        case = self._Case(
                number = number,
                )
        state.ifdepth.append(case)

        commands_logger.debug(r"\ifcase: %s", case)

        if number!=0:
            commands_logger.debug(r"\ifcase on %d; skipping",
                    number)

class Or(C_Conditional):
    def do_conditional(self, tokens):
        try:
            tokens.state.ifdepth[-1].next_case()
        except AttributeError:
            raise mex.exception.MexError(
                    r"can't \or; we're not in an \ifcase block")


