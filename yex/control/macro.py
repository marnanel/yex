"""
Macro controls.

Everything to do with creating macros (TeX's name for functions) lives here.
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

            raise yex.exception.YexError(
                    "internal: macro started and "
                    "ended with different records!")

        found.jump_back(tokens)

    def __repr__(self):
        return f'[return]'

class C_Macro(C_Expandable):
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
                raise yex.exception.MacroError(
                        f"Use of {self.name} doesn't match its definition."
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
        find_which_param = False

        for t in self.definition:

            if find_which_param:
                find_which_param = False

                if t.ch=='#':
                    interpolated.append(t)
                else:
                    # TODO catch param numbers that don't exist
                    interpolated.extend(
                            arguments[int(t.ch)-1],
                            )
            elif isinstance(t, yex.parse.Parameter):
                find_which_param = True
            else:
                interpolated.append(t)

        if find_which_param:
            # self.definition has already been processed,
            # by us, so presumably this shouldn't come up
            raise yex.exception.ParseError(
                    "definition ended with a param sign "
                    "(shouldn't happen)"
                    )

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

    def check_for_par(self, e, unless=False):
        r"""
        Returns an iterator that maybe checks for \par in e.

        If self.long==True, or unless==True, returns e unchanged.

        Otherwise, returns an iterator wrapping e, which passes every item
        straight through, unless it was generated from a control token
        called \par. In that case, it raises RunawayExpansionError.

        Args:
            e: an Expander
        """

        if self.is_long or unless:
            return e

        referent_of_par = self.doc.get(
                r'\par',
                param_control=True,
                default = None,
                )

        logger.debug(r"%s: checking for \par in %s", self, e)
        logger.debug(r"%s: \par == %s", self, e)

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

        return ParChecker(e)

    @classmethod
    def from_serial(cls, state):
        result = cls.__new__(cls)
        result.__setstate__(state)
        return result

##############################

class Def(C_Expandable):

    settings = set(('def',))

    def __call__(self, tokens):

        # Firstly, what flags have been used? There's a lot of them,
        # and they all have "settings" fields. We union them all together.
        # The ones with "def" in the settings field are terminal.

        settings = set(self.settings)

        while 'def' not in settings:

            token = tokens.next(
                    level = 'deep',
                    on_eof='raise',
                    )

            if not isinstance(token, yex.parse.Control):
                raise yex.exception.YexError(
                        fr"expected \def or similar, "
                        f"but got {token}")

            flag = tokens.doc.get(token.identifier,
                    default=None)

            if isinstance(flag, (Def, Global)):
                settings |= flag.settings
            else:
                raise yex.exception.YexError(
                        fr"expected \def or similar, "
                        f"but got {flag}")

        settings.remove('def')

        token = tokens.next(
                level = 'deep',
                on_eof='raise',
                )
        macro_name = token.ch

        logger.debug("defining new macro: %s; settings=%s",
                macro_name, settings,
                )

        if 'global' in settings:
            tokens.doc.next_assignment_is_global = True

        # Next, let's find the parameters.

        definition_extension = []

        try:
            macro_name = token.identifier
        except NotImplementedError:
            raise yex.exception.ParseError(
                    "definition names must be "
                    f"a control sequence or an active character "
                    f"(not {token.meaning})")

        logger.debug("  -- macro name: %s", macro_name)
        parameter_text = [ [] ]
        param_count = 0

        deep = tokens.another(level='deep',
                on_eof='raise',
                )

        for token in deep:
            logger.debug("  -- param token: %s", token)

            if isinstance(token, yex.parse.BeginningGroup):
                deep.push(token)
                break
            elif isinstance(token, yex.parse.Control):
                try:
                    if tokens.doc.controls[token.identifier].is_outer:
                        raise yex.exception.MacroError(
                                "outer macros not allowed in param lists")
                except KeyError:
                    pass # Control doesn't exist, so can't be outer

                parameter_text[-1].append(token)

            elif isinstance(token, yex.parse.Parameter):

                which = deep.next()

                if isinstance(which, yex.parse.BeginningGroup):
                    # Special case. See "A special extension..." on
                    # p204 of the TeXbook.
                    logger.debug(
                            "  -- #{ -- see TeXbook p204: %s", token)
                    parameter_text[-1].append(which)
                    definition_extension.append(which)
                    deep.push(which)
                    break

                elif which.ch not in string.digits:
                    raise yex.exception.ParseError(
                            f"parameters can only be named with digits "
                            f"(not {which})"
                            )

                elif int(which.ch) != param_count+1:
                    raise yex.exception.ParseError(
                            rf"{self.name}\{macro_name}: "
                            "parameters must occur in ascending order "
                            f"(found {which.ch}, needed {param_count+1})"
                            )
                else:
                    parameter_text.append( [] )
                    param_count += 1
            else:
                parameter_text[-1].append(token)

        logger.debug("  -- parameter_text: %s", parameter_text)

        # now the definition
        definition = []

        if 'expanded' in settings:
            level = 'expanding'
        else:
            level = 'deep'

        starts_at = None
        for token in tokens.another(
                bounded='single',
                on_eof='exhaust',
                level = level,
                no_outer=True,
                ):

            logger.debug("  -- definition token: %s", token)
            definition.append(token)
            if starts_at is None:
                starts_at = tokens.location

        definition.extend(definition_extension)
        logger.debug("  -- definition: %s", definition)

        new_macro = C_Macro(
                doc = self.doc,
                name = macro_name,
                definition = definition,
                parameter_text = parameter_text,
                starts_at = starts_at,
                is_outer = 'outer' in settings,
                is_expanded = 'expanded' in settings,
                is_long = 'long' in settings,
                )

        logger.debug("  -- object: %s", new_macro)

        tokens.doc[macro_name] = new_macro

# These are all forms of definition,
# so they're handled as Def.

class Outer(Def):
    settings = set(('outer',))

class Gdef(Def):
    settings = set(('global', 'def'))

class Long(Def):
    settings = set(('long',))

class Edef(Def):
    settings = set(('expanded', 'def'))

class Xdef(Def):
    settings = set(('expanded', 'global', 'def'))

class Global(C_Expandable):
    settings = set(('global', ))
    def __call__(self, tokens):
        tokens.doc.next_assignment_is_global = True
