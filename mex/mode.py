import logging
import mex.box

commands_logger = logging.getLogger('mex.commands')

class Mode:

    is_horizontal = False
    is_vertical = False
    is_math = False
    is_inner = False

    def __init__(self, state):
        self.state = state

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def handle(self, item):
        commands_logger.info("%s: %s",
                self, item)

        if item.category==item.MATH_SHIFT:
            self.state.begin_group()
            self.state['_mode'] = 'math'

    def showlist(self):
        """
        Shows our details, as part of the
        \showlists debugging command.
        See p88 of the TeXbook.
        """
        print(f"### {self}")

    def __repr__(self):
        return f'{self.name} mode'.replace('_', ' ')

class Vertical(Mode):
    is_vertical = True

class Internal_Vertical(Vertical):
    is_inner = True

class Horizontal(Mode):
    is_horizontal = True

    def __init__(self, state):
        super().__init__(state)

        state.box = mex.box.HBox

class Restricted_Horizontal(Horizontal):
    is_inner = True

class Math(Mode):
    is_math = True

class Display_Math(Math):
    is_inner = True

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
