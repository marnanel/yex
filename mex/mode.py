class Mode:
    def __init__(self, state):
        self.state = state

    def handle(self, item):
        pass

class Vertical(Mode):
    pass

class InternalVertical(Vertical):
    pass

class Horizontal(Mode):
    pass

class RestrictedHorizontal(Horizontal):
    pass

class Math(Mode):
    pass

class DisplayMath(Math):
    pass

def handlers(state):

    g = globals().items()

    result = dict([
        (name.lower(), value(state)) for
        (name, value) in g
        if value.__class__==type and
        issubclass(value, Mode) and
        value!=Mode
        ])

    return result
