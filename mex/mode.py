import logging
import mex.box

commands_logger = logging.getLogger('mex.commands')

class Mode:
    def __init__(self, state):
        self.state = state

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def handle(self, item):
        commands_logger.info("%s: %s",
                self, item)

class Vertical(Mode):
    pass

class InternalVertical(Vertical):
    pass

class Horizontal(Mode):

    def __init__(self, state):
        super().__init__(state)

        state.box = mex.box.HBox

class RestrictedHorizontal(Horizontal):
    pass

class Math(Mode):
    pass

class DisplayMath(Math):
    pass

def handlers():

    g = globals().items()

    result = dict([
        (name.lower(), value) for
        (name, value) in g
        if value.__class__==type and
        issubclass(value, Mode) and
        value!=Mode
        ])

    return result
