"""
Macro controls.

These are the classes for macros-- TeX's term for subroutines.
The commands which create these macros live in yex.control.keywords.macro.
"""

import logging
from yex.control.control import *
import yex
import string

logger = logging.getLogger('yex.general')

class _Store_Call(yex.parse.token.Internal):
    """
    Pushes a call frame onto the call stack.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.record = yex.document.Callframe(
                **kwargs,
                )

    def __call__(self, tokens):
        tokens.doc.call_stack.append(self.record)
        logger.debug(
                "call stack: push: %s",
                tokens.doc.call_stack)

    def __repr__(self):
        return f'[call: {self.record}]'

class _Store_Return(yex.parse.token.Internal):
    """
    Pops a frame from the call stack.
    """

    def __init__(self, beginner, *args, **kwargs):
        super().__init__(*args)
        self.expected = beginner.record

    def __call__(self, tokens):
        found = tokens.doc.call_stack.pop()
        logger.debug(
                "call stack: pop : %s",
                found)

        if found != self.expected:
            logger.critical(
                    "call stack mismatch!! expected %s, but found %s",
                    self.expected, found,
                    )

            raise yex.exception.MismatchedMacroRecordsError()

        found.jump_back(tokens)

    def __repr__(self):
        return f'[return]'

class Macro(Expandable):
    r"""
    Any macro defined using \def.
    """

    def __init__(self,
            doc,
            definition,
            parameter_text,
            starts_at,
            *args, **kwargs):

        super().__init__(*args, **kwargs)

        if self.name.startswith('\\'):
            # remove initial backslash; we don't want to double it
            self.name = self.name[1:]

        self.doc = doc
        self.definition = definition
        self.parameter_text = parameter_text
        self.starts_at = starts_at

    def __call__(self, tokens):

        logger.debug('%s: delimiters=%s', self, self.parameter_text)

        try:
            arguments = self._part1_find_arguments(tokens)
        except yex.exception.RunawayExpansionError:
            # we know the name of the macro now, so raise a new error
            raise yex.exception.RunawayExpansionError(self.name)

        logger.debug('%s: arguments=%s', self, arguments)
        interpolated = self._part2_interpolate(arguments)
        logger.debug('%s: result=%s', self, interpolated)

        beginner = _Store_Call(
            callee = self.name,
            args = arguments,
            location = tokens.location,
            )
        ender = _Store_Return(
                beginner = beginner,
                )

        # Push store and return back to front, because these tokens
        # are retrieved first-in-first-out.

        tokens.push(ender, is_result=True)
        tokens.push(interpolated, is_result=True)
        tokens.push(beginner, is_result=True)

        tokens.location = self.starts_at

    def _part1_find_arguments(self, tokens):

        arguments = {}

        if not self.parameter_text:
            return arguments

        tokens = tokens.another(
                no_outer=True,
                level='deep',
                on_eof='exhaust',
                )

        # Match the zeroth delimiter, i.e. the symbols
        # which must appear before any parameter.
        # This should be refactorable into the next part
        # later.
        for tp, te in zip(
                self.parameter_text[0],
                self.check_for_par(tokens)):
            logger.debug("  -- arguments: %s %s", tp, te)
            if tp!=te:
                raise yex.exception.ZerothParameterError(
                        name = self.name,
                        )

        # Now the actual parameters...
        for i, p in enumerate(self.parameter_text[1:]):

            tokens.eat_optional_spaces()

            if p:
                # We're expecting some series of tokens
                # to delimit this argument.

                logger.debug(
                        "%s: argument %s is delimited by %s",
                        self, i, p,
                        )

                looking_for_par = (isinstance(p[0], yex.parse.Control)
                        and p[0].ch==r'\par')

                e = tokens.another(
                    no_outer=True,
                    level='deep',
                    on_eof = 'raise',
                    )

                seen = []
                depth = 0
                balanced = True
                arguments[i] = []

                for j, t in enumerate(self.check_for_par(
                    expander = e,
                    unless = looking_for_par,
                    )):

                    logger.debug(
                            "%s: finding argument %s; token %s is %s",
                            self, i, j, t,
                            )

                    matches = p[len(seen)]==t

                    if isinstance(t, yex.parse.BeginningGroup):
                        if depth==0 and matches:
                            # Special case. If the delimiter itself is {,
                            # we shouldn't count it as starting a new group,
                            # because otherwise we wouldn't match it!
                            beginning_group = False
                        else:
                            beginning_group = True
                    else:
                        beginning_group = False

                    if j==0:
                        # First character in the arguments.
                        if beginning_group:
                            depth = 1
                        else:
                            # First character wasn't an opening brace.
                            # So this text can't be balanced.
                            balanced = False
                    else:
                        # Not the first character.
                        if beginning_group:
                            if depth==0:
                                # Starting a new group from ground level
                                # part-way through an arguments string,
                                # so this text isn't balanced.
                                balanced = False
                            depth += 1
                        elif isinstance(t, yex.parse.EndGroup):
                            depth -= 1
                            if depth==0:
                                seen = []

                    if depth==0 and matches:
                        seen.append(t)
                        logger.debug(
                                (
                                    "matches delimiter for %s; "
                                    "partial delimiter now %s"
                                    ),
                                self, seen)

                        if len(seen)==len(p):
                            # hurrah, done

                            logger.debug(
                                    "  -- hurrah, that's the whole thing")
                            if balanced:
                                arguments[i] = \
                                        arguments[i][1:-1]
                            break
                    elif seen:
                        logger.debug(
                                "  -- not the delimiter after all; push back")
                        e.push(t)
                        for s in reversed(seen[1:]):
                            e.push(s)
                        arguments[i].append(seen[0])
                        seen = []
                    else:
                        arguments[i].append(t)
            else:
                logger.debug(
                        "%s: argument %s is not delimited",
                        self, i,
                        )

                arguments[i] = list(self.check_for_par(tokens.another(
                        bounded='single',
                        on_eof='exhaust',
                        no_outer=True,
                        level='deep',
                        )))

        logger.debug(
                "%s: arguments found: %s",
                self, arguments,
                )

        return arguments

    def _part2_interpolate(self, arguments):

        interpolated = []

        for t in self.definition:

            if isinstance(t, yex.parse.Argument):
                interpolated.extend(
                        arguments[int(t.ch)-1],
                        )
            else:
                interpolated.append(t)

        return interpolated

    def __repr__(self):
        try:
            return f'[{str(self)}]'
        except AttributeError:
            return f'[{self.__class__.__name__}; inchoate]'

    def __str__(self):
        result = f'\\{self.name}:'

        if self.parameter_text:
            result += '('
            for c in self.parameter_text:
                result += str(c)
            result += ')'

        result += ''.join([
            str(x) for x in self.definition
            ])

        return result

    def __getstate__(self):
        result = {
                'macro': self.name,
                'definition': yex.parse.Token.serialise_list(
                    self.definition,
                    strip_singleton=True,
                    ),
                }

        flags = []
        if self.is_long: flags.append('long')
        if self.is_outer: flags.append('outer')

        if flags:
            result['flags'] = ' '.join(flags)

        parameters = [
            yex.parse.Token.serialise_list(x,
                strip_singleton=True,
                )
            for x in self.parameter_text]

        if parameters==[[]]:
            pass
        elif parameters==[[]]*len(parameters):
            result['parameters'] = len(parameters)-1
        else:
            result['parameters'] = parameters

        if self.starts_at is not None:
            result['starts_at'] = self.starts_at.__getstate__()

        return result

    def __setstate__(self, state):

        self.name = state['macro']

        self.definition = yex.parse.Token.deserialise_list(
                state['definition'],
                )

        self.is_long = self.is_outer = False

        for flag in state.get('flags', '').split(' '):
            if not flag:
                pass
            elif flag=='long':
                self.is_long = True
            elif flag=='outer':
                self.is_outer = True
            else:
                raise ValueError(f'Unknown flag: {flag}')

        state_params = state.get('parameters', None)

        if state_params is None:
            parameters = [[]]
        elif isinstance(state_params, int):
            parameters = [[]]*(state_params+1)
        else:
            parameters = state_params

        self.parameter_text = [
            yex.parse.Token.deserialise_list(x)
            for x in parameters]

        if 'starts_at' in state:
            self.starts_at = yex.parse.Location.from_serial(
                    state['starts_at'])
        else:
            self.starts_at = None

        logger.debug('%s: I\'m back', self)

    def check_for_par(self, expander, unless=False):
        r"""
        Returns an iterator that maybe checks for \par in expander.

        If self.long==True, or unless==True, returns expander unchanged.

        Otherwise, returns an iterator wrapping expander, which passes every item
        straight through, unless it was generated from a control token
        called \par. In that case, it raises RunawayExpansionError.

        Args:
            expander: an Expander
        """

        if self.is_long or unless:
            return expander

        referent_of_par = self.doc.get(
                r'\par',
                param_control=True,
                default = None,
                )

        logger.debug(r"%s: checking for \par in %s", self, expander)
        logger.debug(r"%s: \par == %s", self, expander)

        class ParChecker:
            def __init__(self, expander):
                self.expander = expander
                self.iterator = iter(expander)

            def __iter__(self):
                return self

            def __next__(self):
                result = next(self.iterator)
                if isinstance(result,
                        yex.parse.Control) and result.ch==r'\par':
                    logger.debug(r"%s: literal \par token: %s",
                            self, result)
                    raise yex.exception.RunawayExpansionError()

                elif referent_of_par is not None and result==referent_of_par:
                    logger.debug(r"%s: referent of \par: %s",
                            self, result)
                    raise yex.exception.RunawayExpansionError()
                return result

            def __repr__(self):
                return repr(self.expander)[:-1] + ';no_par]'

        return ParChecker(expander)

    @classmethod
    def from_serial(cls, state):
        result = cls.__new__(cls)
        result.__setstate__(state)
        return result
