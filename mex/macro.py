class Macro:

    magic = False

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def syntax(self):
        return []

    def get_params(self, tokeniser, tokens):
        raise ValueError("superclass does nothing useful in itself")

    def __call__(self, tokens):
        raise ValueError("superclass does nothing useful in itself")

class _UserDefined(Macro):

    def __init__(self,
            definition):

        # TODO anything about params
        self.definition = definition

    def __call__(self, state, tokens):
        return self.definition

class Catcode(Macro):

    def get_params(self, tokeniser, tokens):
        n = Number(tokeniser, tokens)
        raise KeyError(n)

    def __call__(self, state, tokens):
        raise ValueError("catcode called")

class Def(Macro):

    def get_params(self, tokeniser, tokens):
        n = Number(tokeniser, tokens)
        raise KeyError(n)

    def __call__(self, state, tokens):
        print('def here!')

        for token in tokens:
            if token.category != token.CONTROL:
                raise ValueError(
                        f"\\def must be followed by a control sequence")
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
                )

        state[f'macro {macro_name}'] = new_macro

        # a definition produces no output of its own
        return []

class Expander:

    def __init__(self, tokeniser):
        self.tokeniser = tokeniser
        self.state = tokeniser.state

        if 'macros' not in self.state.values[-1]:
            add_macros_to_state(self.state)

    def read(self, f):

        tokens = self.tokeniser.read(f)
        for token in tokens:

            if token.category!=token.CONTROL:
                yield token
                continue

            handler = self.state[f'macro {token.name}']

            if handler is None:
                raise KeyError(f"there is no macro called {token.name}")

            for item in handler(state=self.state, tokens=tokens):
                yield item

def add_macros_to_state(state):
    state.add_state(
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
