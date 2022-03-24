import logging
from yex.control.word import *
import yex.parse
import yex.value
import yex.exception
import yex.font
import yex.document
import string

macros_logger = logging.getLogger('yex.macros')
commands_logger = logging.getLogger('yex.commands')

class _Store_Call(yex.parse.token.Internal):
    """
    Pushes a call frame onto the call stack.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.record = yex.document.Callframe(
                **kwargs,
                )

    def __call__(self, name, tokens):
        tokens.doc.call_stack.append(self.record)
        macros_logger.debug(
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

    def __call__(self, name, tokens):
        found = tokens.doc.call_stack.pop()

        if found != self.expected:
            macros_logger.critical(
                    "call stack mismatch!! expected %s, but found %s",
                    self.expected, found,
                    )

            raise yex.exception.YexError(
                    "internal: macro started and "
                    "ended with different records!")


    def __repr__(self):
        return f'[return]'

class C_Macro(C_Defined):
    r"""
    Any macro defined using \def.
    """

    def __init__(self,
            definition,
            parameter_text,
            *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.definition = definition
        self.parameter_text = parameter_text

    def __call__(self, name, tokens):

        macros_logger.debug('%s: delimiters=%s', name, self.parameter_text)

        try:
            arguments = self._part1_find_arguments(name, tokens)
        except yex.exception.RunawayExpansionError:
            # we know the name of the macro now, so raise a new error
            raise yex.exception.RunawayExpansionError(name)

        macros_logger.debug('%s: arguments=%s', name, arguments)
        interpolated = self._part2_interpolate(arguments)
        macros_logger.debug('%s: result=%s', name, interpolated)

        beginner = _Store_Call(
            callee = name,
            args = arguments,
            location = name.location,
            )
        ender = _Store_Return(
                beginner = beginner,
                )

        # Push store and return back to front, because these tokens
        # are retrieved first-in-first-out.

        tokens.push(ender)
        tokens.push(interpolated)
        tokens.push(beginner)

    def _part1_find_arguments(self, name, tokens):

        arguments = {}

        if not self.parameter_text:
            return arguments

        # Match the zeroth delimiter, i.e. the symbols
        # which must appear before any parameter.
        # This should be refactorable into the next part
        # later.
        for tp, te in zip(
                self.parameter_text[0],
                tokens.child(
                    no_outer=True,
                    no_par=not self.is_long,
                    expand=False,
                    on_eof=tokens.EOF_EXHAUST,
                    )):
            macros_logger.debug("  -- arguments: %s %s", tp, te)
            if tp!=te:
                raise yex.exception.MacroError(
                        f"Use of {name} doesn't match its definition."
                        )

        # Now the actual parameters...
        for i, p in enumerate(self.parameter_text[1:]):

            tokens.eat_optional_spaces()

            if p:
                # We're expecting some series of tokens
                # to delimit this argument.

                macros_logger.debug(
                        "%s: argument %s is delimited by %s",
                        name, i, p,
                        )

                e = tokens.child(
                    no_outer=True,
                    no_par=not self.is_long,
                    expand=False,
                    on_eof = tokens.EOF_RAISE_EXCEPTION,
                    )

                seen = []
                depth = 0
                balanced = True
                arguments[i] = []

                for j, t in enumerate(e):

                    macros_logger.debug(
                            "%s: finding argument %s; token %s is %s",
                            name, i, j, t,
                            )

                    matches = p[len(seen)]==t

                    if t.category==t.BEGINNING_GROUP:
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
                        elif t.category==t.END_GROUP:
                            depth -= 1
                            if depth==0:
                                seen = []

                    if depth==0 and matches:
                        seen.append(t)
                        macros_logger.debug(
                                (
                                    "matches delimiter for %s; "
                                    "partial delimiter now %s"
                                    ),
                                name, seen)

                        if len(seen)==len(p):
                            # hurrah, done

                            macros_logger.debug(
                                    "  -- hurrah, that's the whole thing")
                            if balanced:
                                arguments[i] = \
                                        arguments[i][1:-1]
                            break
                    elif seen:
                        macros_logger.debug(
                                "  -- not the delimiter after all; push back")
                        e.push(t)
                        for s in reversed(seen[1:]):
                            e.push(s)
                        arguments[i].append(seen[0])
                        seen = []
                    else:
                        arguments[i].append(t)
            else:
                macros_logger.debug(
                        "%s: argument %s is not delimited",
                        name, i,
                        )

                arguments[i] = list(
                    tokens.single_shot(
                        no_outer=True,
                        no_par=not self.is_long,
                        expand=False,
                        ))

        macros_logger.debug(
                "%s: arguments found: %s",
                name, arguments,
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
            elif isinstance(t, yex.parse.Token) and t.category==t.PARAMETER:
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
        result = f'[\\{self.name}:'

        if self.parameter_text:
            result += '('
            for c in self.parameter_text:
                result += str(c)
            result += ')'

        for c in self.definition:
            result += str(c)

        result += ']'
        return result

class Def(C_Expandable):

    def __call__(self, name, tokens,
        is_outer = False,
        is_long = False,
        is_expanded = False,
        ):

        # Optional arguments may be supplied by Outer,
        # below.

        token = tokens.next(expand=False,
                on_eof=tokens.EOF_RAISE_EXCEPTION)
        macros_logger.debug("defining new macro:")
        macros_logger.debug("  -- macro name: %s", token)

        definition_extension = []

        if token.category==token.CONTROL:
            macro_name = token.name
        elif token.category==token.ACTIVE:
            macro_name = token.ch
        else:
            raise yex.exception.ParseError(
                    f"{name}: "
                    "definition names must be "
                    f"a control sequence or an active character "
                    f"(not {token})")

        parameter_text = [ [] ]
        param_count = 0

        for token in tokens.tokeniser:
            macros_logger.debug("  -- param token: %s", token)

            if token.category == token.BEGINNING_GROUP:
                tokens.push(token)
                break
            elif token.category == token.CONTROL:
                try:
                    if tokens.doc.controls[token.name].is_outer:
                        raise yex.exception.MacroError(
                                rf"{name}\{macro_name}: "
                                "outer macros not allowed in param lists")
                except KeyError:
                    pass # Control doesn't exist, so can't be outer

                parameter_text[-1].append(token)
            elif token.category == token.PARAMETER:

                which = next(tokens.tokeniser)

                if which.category==which.BEGINNING_GROUP:
                    # Special case. See "A special extension..." on
                    # p204 of the TeXbook.
                    macros_logger.debug(
                            "  -- #{ -- see TeXbook p204: %s", token)
                    parameter_text[-1].append(which)
                    definition_extension.append(which)
                    tokens.push(which)
                    break

                elif which.ch not in string.digits:
                    raise yex.exception.ParseError(
                            f"parameters can only be named with digits "
                            f"(not {which.ch})"
                            )

                elif int(which.ch) != param_count+1:
                    raise yex.exception.ParseError(
                            rf"{name}\{macro_name}: "
                            "parameters must occur in ascending order "
                            f"(found {which.ch}, needed {param_count+1})"
                            )
                else:
                    parameter_text.append( [] )
                    param_count += 1
            else:
                parameter_text[-1].append(token)

        macros_logger.debug("  -- parameter_text: %s", parameter_text)

        # now the definition
        definition = []

        for token in tokens.single_shot(
                expand=is_expanded,
                no_outer=True,
                ):
            macros_logger.debug("  -- definition token: %s", token)
            definition.append(token)

        definition.extend(definition_extension)
        macros_logger.debug("  -- definition: %s", definition)

        new_macro = C_Macro(
                name = macro_name,
                definition = definition,
                parameter_text = parameter_text,
                is_outer = is_outer,
                is_expanded = is_expanded,
                is_long = is_long,
                )

        macros_logger.debug("  -- object: %s", new_macro)

        tokens.doc[macro_name] = new_macro

class Outer(C_Expandable):

    """
    This handles all the modifiers which can precede \\def.
    All these modifiers are either this class or one of
    its subclasses.

    This class passes all the actual work on to Def.
    """

    def __call__(self, name, tokens):
        is_outer = False
        is_long = False
        is_expanded = False

        token = name
        e = tokens.not_expanding()

        def _raise_error():
            raise yex.exception.ParseError(
                    rf"\{self.name} must be followed by a "+\
                            f"definition (not {token})")

        while True:
            macros_logger.debug("token: %s", token)
            if token.category != token.CONTROL:
                _raise_error()
            elif token.name=='def':
                break
            elif token.name=='gdef':
                tokens.doc.next_assignment_is_global = True
                break
            elif token.name=='edef':
                is_expanded = True
                break
            elif token.name=='xdef':
                tokens.doc.next_assignment_is_global = True
                is_expanded = True
                break
            elif token.name=='outer':
                is_outer = True
            elif token.name=='long':
                is_long = True
            else:
                _raise_error()

            token = e.next()
            macros_logger.debug("read: %s", token)

        tokens.doc.controls['def'](
                name = name, tokens = tokens,
                is_outer = is_outer,
                is_long = is_long,
                is_expanded = is_expanded,
                )

# These are all forms of definition,
# so they're handled as Def.

class Gdef(Outer): pass
class Long(Outer): pass
class Edef(Outer): pass
class Xdef(Outer): pass

class Global(C_Expandable):
    def __call__(self, name, tokens):
        tokens.doc.next_assignment_is_global = True
