import logging
import mex.token
import mex.value
import mex.exception

macro_logger = logging.getLogger('mex.macros')
command_logger = logging.getLogger('mex.commands')

# XXX Most of this is to do with controls rather than macros
# XXX Split it out.

class Macro:

    def __init__(self,
            is_long = False,
            is_outer = False,
            is_expanded = False,
            name = None,
            *args, **kwargs):

        self.is_long = is_long
        self.is_outer = is_outer
        self.is_expanded = is_expanded

        if name is None:
            self.name = self.__class__.__name__.lower()
        else:
            self.name = name

    def __call__(self, name, tokens):
        raise ValueError("superclass does nothing useful in itself")

    def __repr__(self):
        return f'[\\{self.name}]'

class Variable:
    def __init__(self):
        self.value = None

    def assign_from_tokens(self, tokens):
        # Optional equals
        for token in tokens:
            if token.category==token.SPACE:
                pass
            elif token.category==token.OTHER and token.ch=='=':
                break
            else:
                tokens.push(token)
                break

        self.value = self._read_value(
                Expander(tokens,
                    allow_eof=False,
                    ))

    def _read_value(self, tokens):
        raise ValueError("superclass")

class _UserDefined(Macro):

    def __init__(self,
            definition,
            params,
            *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.definition = definition
        self.params = params

    def __call__(self, name, tokens):

        # Try to find values for our params.
        parameter_values = {}
        i = 0
        current_parameter = None

        through_possible_param_end = 0

        p = self.params

        while i<len(self.params):

            if p[i].category == p[i].PARAMETER:

                current_parameter = p[i].ch
                parameter_values[current_parameter] = []
                i += 1

                # If this parameter is immediately followed by another
                # parameter (or the end of the parameters), then the
                # value is either only one character
                # or a grouping in braces.

                if i>=len(self.params) or p[i].category==p[i].PARAMETER:

                    e = Expander(tokens,
                            single=True,
                            no_outer=True,
                            no_par=not self.is_long,
                            )
                    for token in e:

                        parameter_values[current_parameter].append(token)

                continue

            # So, not a parameter.
            raise ValueError('(not yet implemented)') # TODO

        # Values found. Interpolate them.

        interpolated = []
        for t in self.definition:
            if t.category==t.PARAMETER:
                for t2 in parameter_values[t.ch]:
                    interpolated.append(t2)
            else:
                interpolated.append(t)

        result = []
        for token in Expander(
                mex.token.Tokeniser(
                    state = tokens.state,
                    source = interpolated,
                    )
                ):
            result.append(token)

        return result

    def __repr__(self):
        result = f'[\\{self.name}'

        if self.params:
            result += '('
            for c in self.params:
                result += str(c)
            result += ')'

        for c in self.definition:
            result += str(c)

        result += ']'
        return result

class Catcode(Macro):

    def __call__(self, name, tokens):

        tokens = Expander(tokens,
                allow_eof = False,
                )
        char = chr(mex.value.Number(tokens).value)

        class CatcodeVariable(Variable):

            def __init__(self, state):
                self.state = state

            def _read_value(self, tokens):
                catcode = mex.value.Number(tokens).value

                self.state.set_catcode(
                        char = char,
                        catcode = catcode,
                        )

        return [CatcodeVariable(tokens.state)]

class Def(Macro):

    def __call__(self, name, tokens,
        is_global = False,
        is_outer = False,
        is_long = False,
        is_expanded = False,
        ):

        # Optional arguments may be supplied by Outer,
        # below.

        token = tokens.__next__()
        macro_logger.info("macro name: %s", token)

        if token.category != token.CONTROL:
            raise mex.exception.ParseError(
                    f"definition names must be "+\
                            f"a control sequence (not {token})",
                            tokens)
        macro_name = token.name

        params = []

        for token in tokens:
            if token.category == token.BEGINNING_GROUP:
                tokens.push(token)
                break
            elif token.category == token.CONTROL and \
                    tokens.state.controls[token.name].is_outer:
                        raise mex.exception.ParseError(
                                "outer macros not allowed in param lists",
                                tokens.state)
            else:
                # TODO check that params are in the correct order
                # (per TeXbook)
                params.append(token)

        # now the definition

        definition = []

        for token in Expander(tokens,
                running=False,
                single=True,
                ):
            if token.category == token.CONTROL and \
                    tokens.state.controls[token.name].is_outer:
                        raise mex.exception.ParseError(
                                "outer macros not allowed in definitions",
                                tokens.state)
            definition.append(token)

        new_macro = _UserDefined(
                name = macro_name,
                definition = definition,
                params = params,
                is_global = is_global,
                is_outer = is_outer,
                is_expanded = is_expanded,
                is_long = is_long,
                )

        tokens.state.set(
               field = macro_name,
               value = new_macro,
               use_global = is_global,
               block = 'controls',
               )

class Outer(Macro):

    """
    This handles all the modifiers which can precede \\def.
    All these modifiers are either this class or one of
    its subclasses.

    This class passes all the actual work on to Def.
    """

    def __call__(self, name, tokens):
        is_global = False
        is_outer = False
        is_long = False
        is_expanded = False

        token = name
        while True:
            if token is None or token.category != token.CONTROL:
                # XXX this message will be too confusing in
                # XXX many circumstances
                raise mex.exception.ParseError(
                        f"definitions must be followed by "+\
                                f"a control sequence (not {token})",
                                tokens)

            if token.name=='def':
                break
            elif token.name=='gdef':
                is_global = True
                break
            elif token.name=='edef':
                is_expanded = True
                break
            elif token.name=='xdef':
                is_expanded = True
                is_global = True
                break
            elif token.name=='global':
                is_global = True
            elif token.name=='outer':
                is_outer = True
            elif token.name=='long':
                is_long = True
            else:
                token = None
                continue

            token = tokens.__next__()
            macro_logger.info("read: %s", token)

        tokens.state.controls['def'](
                name = name, tokens = tokens,
                is_global = is_global,
                is_outer = is_outer,
                is_long = is_long,
                is_expanded = is_expanded,
                )

# These are all forms of definition,
# so they're handled as Def.

class Gdef(Outer): pass
class Global(Outer): pass # XXX "Global" can also precede simple defs
class Outer(Outer): pass
class Long(Outer): pass
class Edef(Outer): pass
class Xdef(Outer): pass

class Chardef(Macro):

    def __call__(self, name, tokens):

        is_global = False
        is_outer = False
        is_long = False
        is_expanded = False

        tokens.running = False
        newname = tokens.__next__()
        tokens.running = True

        if newname.category != newname.CONTROL:
            raise mex.exception.ParseError(
                    f"chardef must be followed by a control, not {token}",
                    tokens)

        char = chr(mex.value.Number(tokens).value)

        # XXX do we really want to allow them to redefine
        # XXX *any* control?

        class Redefined_by_chardef(Macro):

            def __call__(self, name, tokens):
                tokens.push(char)

            def __repr__(self):
                return f"[{char}]"

        tokens.state.set(
                field = newname.name,
                value = Redefined_by_chardef(),
                block = 'controls',
                )

class Par(Macro):
    def __call__(self, name, tokens):
        pass

class Expander:

    """
    Takes a Tokeniser, and iterates over it,
    yielding the tokens with the macros expanded
    according to the definitions
    stored in the State attached to that Tokeniser.

    It's fine to attach another Expander to the
    same Tokeniser, and to run it even when this
    one is in the middle of a yield.

    Parameters:
        tokens  -   the Tokeniser
        single  -   if True, iteration stops after a single
                    character, or a balanced group if the
                    next character is a BEGINNING_GROUP.
                    If False (the default), iteration ends when the
                    Tokeniser ends.
        running -   if True (the default), expand macros.
                    If False, pass everything straight through.
                    This may be adjusted mid-run.
        allow_eof - if True (the default), end iteration at
                    the end of the file.
                    If False, continue returning None forever.
        no_outer -  if True, attempting to call a macro which
                    was defined as "outer" will cause an error.
                    Defaults to False.
        no_par -    if True, the "par" token is forbidden--
                    that is, any control whose name is "\\par",
                    not necessarily our own Par class.
                    Defaults to False.
    """

    def __init__(self, tokens,
            single = False,
            running = True,
            allow_eof = True,
            no_outer = False,
            no_par = False,
            ):

        self.tokens = tokens
        self.state = tokens.state
        self.single = single
        self.single_grouping = 0
        self.running = running
        self.allow_eof = allow_eof
        self.no_outer = no_outer
        self.no_par = no_par

        self._iterator = self._read()

    def __iter__(self):
        return self

    def __next__(self):
        return self._iterator.__next__()

    def _read(self):

        while True:

            try:
                token = self.tokens.__next__()
            except StopIteration:

                if self.tokens.push_back:
                    token = self.tokens.push_back.pop()
                elif self.allow_eof:
                    return
                else:
                    token = None

            if self.no_par:
                if token.category==token.CONTROL and token.name=='par':
                    raise mex.exception.ParseError(
                            "runaway expansion",
                            self.state)

            if self.single:
                if token.category==token.BEGINNING_GROUP:
                    self.single_grouping += 1

                    if self.single_grouping!=1:
                        yield token
                    continue
                elif self.single_grouping==0:
                    # First token wasn't a BEGINNING_GROUP,
                    # so we yield that and then stop.
                    yield token
                    return

                if token.category==token.END_GROUP:
                    self.single_grouping -= 1
                    if self.single_grouping==0:
                        return

            if not self.running:
                yield token
                continue

            if token is None:
                yield token

            elif isinstance(token, mex.macro.Variable):
                token.assign_from_tokens(self.tokens)

            elif token.category==token.CONTROL:
                handler = self.state.controls.get(token.name, None)

                if handler is None:
                    if len(token.name)==1:
                        # they used a control symbol which
                        # doesn't exist, so just give them
                        # the literal symbol they typed
                        self.push(
                                mex.token.Token(
                                    category = mex.token.Token.OTHER,
                                    ch = token.name,
                                    ))
                    else:
                        raise KeyError(f"there is no macro called {token.name}")
                elif self.no_outer and handler.is_outer:
                    raise mex.exception.ParseError(
                            "outer macro called where it shouldn't be",
                            self.state)
                else:
                    macro_logger.info('Calling macro: %s', handler)
                    # control exists, so run it.
                    handler_result = handler(
                            name = token,
                            tokens=self.tokens,
                            )

                    if handler_result:
                        self.tokens.push(handler_result)
            else:
                yield token

    def push(self, token):

        if token is None:
            return

        self.tokens.push(token)

def handlers():

    # Take a copy. Sometimes evaluating a macro may
    # create another macro, which changes the size
    # of globals().items() and confuses the list comprehension.
    g = list(globals().items())

    result = dict([
            (name.lower(), value()) for
            (name, value) in g
            if value.__class__==type and
            value!=Macro and
            issubclass(value, Macro) and
            not name.startswith('_')
            ])

    return result
