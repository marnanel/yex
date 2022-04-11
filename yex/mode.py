import logging
import yex.box
import yex.gismo
from yex.parse import *

logger = logging.getLogger('yex.commands')

class Mode:

    is_horizontal = False
    is_vertical = False
    is_math = False
    is_inner = False

    def __init__(self, doc):
        self.doc = doc
        self.list = []

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def handle(self, item, tokens):
        """
        Handles incoming items. The rules are on p278 of the TeXbook.
        """

        if isinstance(item, BeginningGroup):
            self.doc.begin_group()

        elif isinstance(item, EndGroup):
            try:
                self.doc.end_group()
            except ValueError as ve:
                raise yex.exception.ParseError(
                        str(ve))

        elif isinstance(item, (Control, Active)):
            handler = self.doc.get(
                    field=item.identifier,
                    default=None,
                    tokens=tokens)

            logger.debug("%s: %s: handler is %s",
                    self, item, handler
                    )

            if handler is None:
                logger.critical(
                        "%s: %s has no handler!",
                        self, str(item),
                        )

                raise yex.exception.YexError(
                        f"{item.identifier} has no handler!",
                        )

            handler(tokens = tokens)

        elif isinstance(item, Paragraph):

            pass # TODO

        elif isinstance(item, Token):

            # any other kind of token

            self._handle_token(item, tokens)

        elif isinstance(item, (
                yex.control.C_Control,
                yex.register.Register,
                )):

            item(tokens = tokens)

        elif isinstance(item, yex.gismo.Gismo):
            if item.is_void():
                logger.debug("%s: %s: void; ignoring",
                        self, item,
                        )
            else:

                # self.list.append( interline glue ) # FIXME
                self.list.append(item)
                # self.list.append( material that migrates ) # FIXME

                self.exercise_page_builder()

        else:
            raise ValueError(
                    f"What do I do with {item} of type {type(item)}?")

    def run_single(self, tokens):
        """
        Reads a single piece of code from `tokens`.

        The code is delimited by `{` and `}` (or other chars which are
        set to those categories). Even so, the code isn't enclosed in
        a group: whatever it changes will stay changed.

        Args:
            tokens (`Expander`): the tokens to read and run.

        Returns:
            the list of tokens received.
        """
        token = tokens.next()

        if isinstance(token, yex.parse.BeginningGroup):
            tokens.push(token) # good
        else:
            raise yex.exception.YexError(
                    f"{self.identifier} must be followed by "
                    "'{'"
                    f"(not {token.meaning})")

        previous_list = self.list
        self.list = []

        logger.debug("%s: run_single: gathering the tokens",
                self,
                )
        for token in tokens.another(
                on_eof='exhaust',
                level='executing',
                single=True,
                ):
            self.handle(
                    item=token,
                    tokens=tokens,
                    )
            logger.debug("%s: run_single:   -- handled %s",
                    self,
                    token,
                    )

        result = self.list
        self.list = previous_list

        logger.debug("%s: run_single:   -- result is %s",
                self,
                result,
                )

        return result

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

        self.doc.mode.goodbye()

        self.doc['_mode'] = new_mode
        self.doc.mode.handle(item, tokens)

    def _handle_token(self, item, tokens):
        raise NotImplementedError()

    def __repr__(self):
        return f'{self.name} mode'.replace('_', ' ')

    def append(self, new_thing):
        self.list.append(
                new_thing,
                )
        logger.debug("%s: added %s to list",
                self, new_thing,
                )

    def exercise_page_builder(self):
        # this is a no-op in every mode but Vertical
        pass

    def goodbye(self):
        """
        Called when we're about to switch to a different mode.
        """
        logger.debug("%s: goodbye!")

class Vertical(Mode):
    is_vertical = True

    def __init__(self, doc):
        super().__init__(doc)
        self.contribution_list = []

    def exercise_page_builder(self):
        logger.info("%s: page builder exercised",
                self) # TODO

    def _handle_token(self, item, tokens):
        if isinstance(item, (Letter, Other)):
            self._switch_mode(
                    new_mode='horizontal',
                    item=item,
                    tokens=tokens)

        elif isinstance(item, (Superscript, Subscript)):

            raise yex.exception.ParseError(
                    f"You can't use {item} in {self}.",
                    )

        elif isinstance(item, Space):

            pass # nothing

        else:
            raise ValueError(f"What do I do with token {item}?")

class Internal_Vertical(Vertical):
    is_inner = True

class Horizontal(Mode):
    is_horizontal = True

    def __init__(self, doc):
        super().__init__(doc)

        self.box = yex.box.HBox()

    def _handle_token(self, item, tokens):
        if isinstance(item, Letter):

            current_font = tokens.doc['_font']

            wordbox = None
            try:
                if isinstance(self.list[-1], yex.box.WordBox):
                    wordbox = self.list[-1]
                    if wordbox.font != current_font:
                        wordbox = None
            except IndexError:
                pass

            if wordbox is None:
                wordbox = yex.box.WordBox(
                    font = current_font,
                        )
                self.append(wordbox)

            wordbox.append(item.ch)
            logger.debug(
                    "%s: added %s to wordbox: %s",
                    self, item, wordbox,
                    )

        elif isinstance(item, Other):
            self.append(
                    yex.box.CharBox(
                        ch = item.ch,
                        font = tokens.doc['_font'],
                        ),
                    )

        elif isinstance(item, (Superscript, Subscript)):

            raise yex.exception.ParseError(
                    f"You can't use {item} in {self}.",
                    )

        elif isinstance(item, Space):

            self.append(
                yex.gismo.Leader(),
                )
        else:
            raise ValueError(f"What do I do with token {item}?")

class Restricted_Horizontal(Horizontal):
    is_inner = True

class Math(Mode):
    is_math = True
    is_inner = True

    def handle(self, item, tokens):

        if isinstance(item, MathShift):
            self.doc.begin_group()
            self.doc['_mode'] = 'display_math'
            return

        super().handle(item, tokens)

    def _handle_token(self, item, tokens):
        pass

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
