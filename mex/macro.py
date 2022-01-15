class Macro:

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def syntax(self):
        return []

    def get_params(self, tokeniser, tokens):
        raise ValueError("superclass does nothing useful in itself")

    def __call__(self):
        raise ValueError("superclass does nothing useful in itself")

class Catcode(Macro):

    def get_params(self, tokeniser, tokens):
        n = Number(tokeniser, tokens)
        raise KeyError(n)

    def __call__(self):
        raise ValueError("catcode called")

def add_macros_to_state(state):
    state.add_state(
            'macro',
            names(),
            )

def names():

    result = dict([
            (name.lower(), value) for
            (name, value) in globals().items()
            if value.__class__==type and
            value!=Macro and
            issubclass(value, Macro)
            ])

    return result
