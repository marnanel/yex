import logging
from mex.control.word import C_ControlWord
import mex.parse
import mex.value
import mex.exception
import mex.font
import sys

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')

class C_UserDefined(C_ControlWord):

    def __init__(self,
            definition,
            parameter_text,
            *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.definition = definition
        self.parameter_text = parameter_text

    def __call__(self, name, tokens):

        macros_logger.debug('%s: delimiters=%s', name, self.parameter_text)
        arguments = self._part1_find_arguments(name, tokens)
        macros_logger.debug('%s: arguments=%s', name, arguments)
        interpolated = self._part2_interpolate(arguments)
        macros_logger.debug('%s: result=%s', name, interpolated)

        tokens.push(interpolated)

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
                raise mex.exception.MacroError(
                        f"Use of {name} doesn't match its definition."
                        )

        # Now the actual parameters...
        for i, p in enumerate(self.parameter_text[1:]):

            macros_logger.debug("  -- params: %s %s", i, p)
            tokens.eat_optional_spaces()

            if p:
                # We're expecting some series of tokens
                # to delimit this argument.

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

                    if j==0:
                        if t.category==t.BEGINNING_GROUP:
                            depth = 1
                        else:
                            balanced = False
                    else:
                        if t.category==t.BEGINNING_GROUP:
                            if depth==0:
                                balanced = False
                            depth += 1
                        elif t.category==t.END_GROUP:
                            depth -= 1
                            if depth==0:
                                seen = []

                    if depth==0 and p[len(seen)]==t:
                        seen.append(t)

                        if len(seen)==len(p):
                            # hurrah, done
                            if balanced:
                                arguments[i] = \
                                        arguments[i][1:-1]
                            break
                    elif seen:
                        e.push(t)
                        for s in reversed(seen[1:]):
                            e.push(s)
                        arguments[i].append(seen[0])
                        seen = []
                    else:
                        arguments[i].append(t)
            else:
                # Not delimited
                arguments[i] = list(
                    tokens.single_shot(
                        no_outer=True,
                        no_par=not self.is_long,
                        expand=False,
                        ))

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
            elif t.category==t.PARAMETER:
                find_which_param = True
            else:
                interpolated.append(t)

        if find_which_param:
            # self.definition has already been processed,
            # by us, so presumably this shouldn't come up
            raise mex.exception.ParseError(
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

class Def(C_ControlWord):

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

        if token.category==token.CONTROL:
            macro_name = token.name
        elif token.category==token.ACTIVE:
            macro_name = token.ch
        else:
            raise mex.exception.ParseError(
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
                    if tokens.state.controls[token.name].is_outer:
                        raise mex.exception.MacroError(
                                rf"{name}\{macro_name}: "
                                "outer macros not allowed in param lists")
                except KeyError:
                    pass # Control doesn't exist, so can't be outer

                parameter_text[-1].append(token)
            elif token.category == token.PARAMETER:

                for which in tokens:
                    break

                if which.category==which.BEGINNING_GROUP:
                    # Special case. See "A special extension..." on
                    # p204 of the TeXbook.
                    macros_logger.debug(
                            "  -- #{ -- see TeXbook p204: %s", token)
                    parameter_text[-1].append(which)

                    tokens.push(which)
                    break

                elif int(which.ch) != param_count+1:
                    raise mex.exception.ParseError(
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

        new_macro = C_UserDefined(
                name = macro_name,
                definition = definition,
                parameter_text = parameter_text,
                is_outer = is_outer,
                is_expanded = is_expanded,
                is_long = is_long,
                )

        macros_logger.debug("  -- definition: %s", definition)
        macros_logger.debug("  -- object: %s", new_macro)

        tokens.state[macro_name] = new_macro

class Outer(C_ControlWord):

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

        def _raise_error():
            raise mex.exception.ParseError(
                    rf"\{self.name} must be followed by a "+\
                            f"definition (not {token})")

        while True:
            if token.category != token.CONTROL:
                _raise_error()
            elif token.name=='def':
                break
            elif token.name=='gdef':
                tokens.state.next_assignment_is_global = True
                break
            elif token.name=='edef':
                is_expanded = True
                break
            elif token.name=='xdef':
                tokens.state.next_assignment_is_global = True
                is_expanded = True
                break
            elif token.name=='outer':
                is_outer = True
            elif token.name=='long':
                is_long = True
            else:
                _raise_error()

            token = tokens.next()
            macros_logger.debug("read: %s", token)

        tokens.state.controls['def'](
                name = name, tokens = tokens,
                is_outer = is_outer,
                is_long = is_long,
                is_expanded = is_expanded,
                )

# These are all forms of definition,
# so they're handled as Def.

class Gdef(Outer): pass
class Outer(Outer): pass
class Long(Outer): pass
class Edef(Outer): pass
class Xdef(Outer): pass

class Global(C_ControlWord):
    def __call__(self, name, tokens):
        tokens.state.next_assignment_is_global = True

#############

