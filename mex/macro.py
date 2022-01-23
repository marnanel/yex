class Macro:

    def __init__(self,
            is_long = False,
            is_outer = False,
            is_expanded = False,
            *args, **kwargs):

        self.is_long = is_long
        self.is_outer = is_outer
        self.is_expanded = is_expanded

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def syntax(self):
        return []

    def get_params(self, tokens):
        raise ValueError("superclass does nothing useful in itself")

    def __call__(self, tokens):
        raise ValueError("superclass does nothing useful in itself")

    def __repr__(self):
        return f'[\\{self.name}]'

class _UserDefined(Macro):

    def __init__(self,
            definition,
            *args, **kwargs):

        super().__init__(*args, **kwargs)

        # TODO anything about params
        self.definition = definition

    def __call__(self, tokens):
        tokens.__next__() # skip our own name
        return self.definition

    def __repr__(self):
        result = f'[\\{self.name}'

        for c in self.definition:
            result += str(c)

        result += ']'
        return result

class Catcode(Macro):

    def get_params(self, tokens):
        n = Number(tokens)
        raise KeyError(n)

    def __call__(self, tokens):
        raise ValueError("catcode called")

class Def(Macro):

    def get_params(self, tokens):
        n = Number(tokens)
        raise KeyError(n)

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

        # now parameters
        for token in tokens:
            if token.category == token.BEGINNING_GROUP:
                break
            else:
                raise ValueError("Please implement parameters")

        # now the definition
        grouping_level = 1
        definition = []

        for token in tokens:
            if token.category == token.BEGINNING_GROUP:
                grouping_level += 1
            elif token.category == token.END_GROUP:
                grouping_level -= 1
                if grouping_level == 0:
                    break

            definition.append(token)

        new_macro = _UserDefined(
                definition = definition,
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

    def __init__(self, tokens):
        self.tokens = tokens
        self.state = tokens.state

        add_macros_to_state(self.state)

        self._iterator = self._read()

    def __iter__(self):
        return self

    def __next__(self):
        return self._iterator.__next__()

    def _read(self):

        for token in self.tokens:

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
