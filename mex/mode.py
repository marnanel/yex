import logging
import mex.box
import mex.debug_plot

logger = logging.getLogger('mex.commands')

class Mode:

    is_horizontal = False
    is_vertical = False
    is_math = False
    is_inner = False

    def __init__(self, state):
        self.state = state
        self.list = []

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def handle(self, item, tokens):
        """
        Handles incoming items. The rules are on p278 of the TeXbook.
        """

        if isinstance(item, mex.parse.Token):
            if item.category==item.BEGINNING_GROUP:
                self.state.begin_group()
            elif item.category==item.END_GROUP:
                try:
                    self.state.end_group()
                except ValueError as ve:
                    raise mex.exception.ParseError(
                            str(ve))
            else:
                self._handle_token(item, tokens)

            return

        elif isinstance(item, mex.box.Box):
            if item.is_void():
                logger.debug("%s: %s: void; ignoring",
                        self, item,
                        )
                return

            # self.list.append( interline glue ) # FIXME
            self.list.append(item)
            # self.list.append( material that migrates ) # FIXME

            self.exercise_page_builder()
            return

        elif isinstance(item, mex.control.C_Unexpandable):

            mode_name = self.__class__.__name__.lower()

            if item.in_modes[mode_name]==False:
                raise mex.exception.ParseError(
                        f"{self}: {item} doesn't work in this mode",
                        )
            elif isinstance(item.in_modes[mode_name], str):
                self._switch_mode(
                        new_mode=item.in_modes[mode_name],
                        item=item,
                        tokens=tokens)
                return

            logger.debug("%s: %s: running",
                    self, item)

            self.item(
                    mode=self,
                    tokens=tokens,
                    )
            return

        raise ValueError(f"What do I do with {item} of type {type(item)}?")

    def showlist(self):
        r"""
        Shows our details, as part of the
        \showlists debugging command.
        See p88 of the TeXbook.
        """
        print(f"### {self}")

    def _switch_mode(self, new_mode, item, tokens):
        """
        Switches the current mode to "new_mode", and
        re-submits the item and tokens to the handler
        of the new mode.

        You should return immediately after calling this.
        """
        logger.debug("%s: %s: switching to %s",
                self, item, new_mode)

        self.state['_mode'] = new_mode
        self.state.mode.handle(item, tokens)

    def _handle_token(self, item, tokens):
        raise NotImplementedError()

    def __repr__(self):
        return f'{self.name} mode'.replace('_', ' ')

class Vertical(Mode):
    is_vertical = True

    def __init__(self, state):
        super().__init__(state)
        self.contribution_list = []

    def exercise_page_builder():
        logger.info("%s: page builder exercised",
                self) # TODO

    def _handle_token(self, item, tokens):
        if item.category in (
                item.LETTER,
                item.OTHER,
                ):
            self._switch_mode(
                    new_mode='horizontal',
                    item=item,
                    tokens=tokens)
            return

        elif item.category==item.SPACE:
            return # nothing

        elif item.category==item.CONTROL:
            handler = self.state.get(
                    field=item.name,
                    default=None,
                    tokens=tokens)
            logger.debug("%s: %s: handler is %s",
                    self, item, handler
                    )
            if handler is None:
                logger.critical(
                        "%s: control word %s has no handler!",
                        self, item,
                        )

                raise mex.exception.MexError(
                        f"token {item} has no handler!",
                        )

            handler(
                    name = item.name,
                    mode = self,
                    tokens = tokens,
                    )
        else:
            raise ValueError(f"What do I do with token {item}?")

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

class Restricted_Horizontal(Horizontal):
    is_inner = True

class Math(Mode):
    is_math = True
    is_inner = True

    def handle(self, item, tokens):
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
