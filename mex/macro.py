import mex.token

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

    def __call__(self, tokens):
        raise ValueError("superclass does nothing useful in itself")

    def __repr__(self):
        return f'[\\{self.name}]'

class _UserDefined(Macro):

    def __init__(self,
            definition,
            params,
            *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.definition = definition
        self.params = params

    def __call__(self, tokens):
        tokens.__next__() # skip our own name

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

                    for token in Expander(tokens,
                            single=True,
                            ):
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

    def __call__(self, tokens):
        raise ValueError("catcode called")

class Def(Macro):

    def __call__(self, tokens):

        is_global = False
        is_outer = False
        is_long = False
        is_expanded = False

        for token in tokens:
            if token.category != token.CONTROL:
                # XXX this message will be too confusing in
                # XXX many circumstances
                raise ValueError(
                        f"definitions must be followed by a control sequence")

            if token.name=='def':
                pass
            elif token.name in ('gdef', 'global'):
                is_global = True
            elif token.name=='outer':
                is_outer = True
            elif token.name=='long':
                is_long = True
            elif token.name=='edef':
                is_expanded = True
            elif token.name=='xdef':
                is_expanded = True
                is_global = True
            else:
                # we've reached the name of the new macro
                macro_name = token.name
                break

        params = []

        # now parameters

        for token in tokens:
            if token.category == token.BEGINNING_GROUP:
                tokens.push(token)
                break
            else:
                # TODO check that params are in the correct order
                # (per TeXbook)
                params.append(token)

        # now the definition

        definition = []

        for token in Expander(tokens,
                single=True,
                running=False,
                ):
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
               field = f'macro {macro_name}',
               value = new_macro,
               use_global = is_global,
               )

        # a definition produces no output of its own
        return []

# These are all forms of definition,
# so they're handled as Def.

class Gdef(Def): pass
class Global(Def): pass
class Outer(Def): pass
class Long(Def): pass
class Edef(Def): pass
class Xdef(Def): pass

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
    """

    def __init__(self, tokens,
            single = False,
            running = True):

        self.tokens = tokens
        self.state = tokens.state
        self.single = single
        self.single_grouping = 0
        self.running = running

        add_macros_to_state(self.state)

        self._iterator = self._read()

    def __iter__(self):
        return self

    def __next__(self):
        return self._iterator.__next__()

    def _read(self):

        for token in self.tokens:

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

            if token.category!=token.CONTROL:
                yield token
                continue

            handler = self.state[f'macro {token.name}']

            if handler is None:
                raise KeyError(f"there is no macro called {token.name}")

            self.tokens.push(token)

            for item in handler(tokens=self.tokens):
                yield item

def add_macros_to_state(state):

    if 'macro' not in state:
        state.add_block(
                'macro',
                names(),
                )

def names():

    result = dict([
            (name.lower(), value()) for
            (name, value) in globals().items()
            if value.__class__==type and
            value!=Macro and
            issubclass(value, Macro) and
            not name.startswith('_')
            ])

    return result
