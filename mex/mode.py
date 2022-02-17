import logging
import mex.box
import mex.debug_plot

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
        r"""
        Shows our details, as part of the
        \showlists debugging command.
        See p88 of the TeXbook.
        """
        print(f"### {self}")

    def __repr__(self):
        return f'{self.name} mode'.replace('_', ' ')

class Vertical(Mode):
    is_vertical = True

    def handle(self, item):
        super().handle(item)

        if item.category in (
                item.LETTER,
                item.MATH_SHIFT,
                ):
            self.state['_mode'] = 'horizontal'
            self.state.mode.handle(item)

class Internal_Vertical(Vertical):
    is_inner = True

class Horizontal(Mode):
    is_horizontal = True

    def __init__(self, state):
        super().__init__(state)

        self.box = mex.box.HBox()

    def showlist(self):
        super().showlist()
        plotter = mex.debug_plot.Debug_Plot('test.html')
        self.box.debug_plot(0, self.box.height+self.box.depth, plotter)
        plotter.close()

    def handle(self, item):
        font = self.state['_currentfont'].value
        charmetrics = font.char_table[ord(item.ch)]

        self.box.append(
                mex.box.CharBox(
                    charmetrics,
                    ),
                )

class Restricted_Horizontal(Horizontal):
    is_inner = True

class Math(Mode):
    is_math = True
    is_inner = True

    def handle(self, item):
        super().handle(item)

        if item.category==item.MATH_SHIFT:
            self.state.begin_group()
            self.state['_mode'] = 'display_math'

class Display_Math(Math):
    is_inner = False

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
