class Macro:

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def syntax(self):
        return []

    def __call__(self):
        raise ValueError("superclass does nothing useful in itself")

class Catcode(Macro):

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
