import logging
import yex.box
import yex.box
import yex.value
from yex.parse import *

logger = logging.getLogger('yex.general')

class Mode:

    is_horizontal = False
    is_vertical = False
    is_math = False
    is_inner = False

    def __init__(self, doc,
            list_obj = None,
            ):

        self.doc = doc

        if list_obj is None:
            self.list = self.our_type()
        else:
            if not isinstance(list_obj, self.our_type):
                raise ValueError(f"list object is {list_obj}, "
                        f"which is not of type {self.our_type}")
            self.list = list_obj

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def handle(self, item,
            tokens = None,
            ):
        """
        Handles incoming items. The rules are on p278 of the TeXbook.
        """

        if isinstance(item, BeginningGroup):
            logger.debug("%s: beginning a group", self)

            self.doc.begin_group()

        elif isinstance(item, EndGroup):
            logger.debug("%s: and ending a group", self)

            a = """900
            if self.list:

                logger.debug("%s:   -- but first, handling %s(%s)",
                        self, tokens.doc.target, self.list)

                if tokens.doc.target is None:
                    raise ValueError(
                            "Don't know what to do with result of mode!: "
                            f"{self.list}"
                            )
                else:
                    tokens.doc.target(tokens, self.list)
                    self.list = None
            """

            try:
                self.doc.end_group(tokens=tokens)
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

        elif isinstance(item, Token):

            # any other kind of token

            self._handle_token(item, tokens)

        elif isinstance(item, (
                yex.control.C_Control,
                yex.register.Register,
                )):

            item(tokens = tokens)

        elif self.doc.hungry:
            handler = self.doc.hungry.pop()

            logger.debug("%s: document is hungry: calling %s with %s",
                    self, handler, item
                    )

            handler(tokens, item)

        elif isinstance(item, yex.box.Gismo):
            if item.is_void():
                logger.debug("%s: %s: void; ignoring",
                        self, item,
                        )
            else:

                self.append(item)
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

    def _switch_mode(self, new_mode, item, tokens,
            target = None,
            ):
        """
        Switches the current mode, and resubmits the item to the new mode.

        You should return immediately after calling this.

        Args:
            new_mode (`Mode` or `str`): the mode to switch to.
                This is simply submitted to `doc["_mode"]`, which see.
            item (any): the item we just read from `tokens`. It will
                be automatically submitted to the `handle()` method
                of the new mode.
            tokens (`Expander`): the token stream.
            target (callable or `None`): function to call with the
                result of this mode (such as an hbox, which the function
                could put inside an enclosing vbox). The value of this
                argument will simply be passed through
                to `self.doc['_target']` without further processing.
                If this is `None`, which is the default, no target is set,
                and if the new mode produces no output it will throw an error.
        """
        logger.debug("%s: %s: switching to %s",
                self, item, new_mode)

        self.doc['_mode'] = new_mode

        if target is not None:
            self.doc['_target'] = target

        self.doc.mode.handle(item, tokens)

    def _handle_token(self, item, tokens):
        raise NotImplementedError()

    def __repr__(self):
        return f'{self.name} mode'.replace('_', ' ')

    def append(self, item, tokens=None):
        self.list.append(
                item,
                )
        logger.debug("%s: added %s to list",
                self, item,
                )

    def exercise_page_builder(self):
        # this is a no-op in every mode but Vertical
        pass

class Vertical(Mode):
    is_vertical = True
    our_type = yex.box.VBox

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contribution_list = []
        self.doc[r'\prevdepth'] = yex.value.Dimen(-1000, 'pt')

    def exercise_page_builder(self):
        logger.info("%s: page builder exercised",
                self)

        self.doc[r'\box255'] = self.list
        self.list = self.our_type()

        group = self.doc.begin_group()

        self.doc.read(
                self.doc[r'\output'].value,
                level = 'executing',
                )

        self.doc.end_group(group = group)

    def _handle_token(self, item, tokens):

        if isinstance(item, (Letter, Other)):

            tokens.doc.begin_group(flavour='only-mode',
                    ephemeral = True)

            self._switch_mode(
                    new_mode='horizontal',
                    item=item,
                    tokens=tokens,
                    target=self.handle,
                    )

        elif isinstance(item, (Superscript, Subscript)):

            raise yex.exception.ParseError(
                    f"You can't use {item} in {self}.",
                    )

        elif isinstance(item, Paragraph):

            pass # nothing

        elif isinstance(item, Space):

            pass # nothing

        else:
            raise ValueError(f"What do I do with token {item}?")

    def append(self, item, tokens=None):

        # This algorithm is given on pp79-80 of the TeXbook.

        prevdepth = self.doc[r'\prevdepth'].value
        baselineskip = self.doc[r'\baselineskip'].value
        basic_skip = baselineskip.space - prevdepth - item.height

        if prevdepth <= yex.value.Dimen(-1000):
            logger.debug("%s: we don't need any extra padding for %s: "
                    "%s<=-1000pt",
                self, item, prevdepth)

        elif basic_skip < self.doc[r'\lineskip'].value.space:
            addendum = yex.box.Leader(
                    space = basic_skip,
                    stretch = baselineskip.stretch,
                    shrink = baselineskip.shrink,
                    )
            logger.debug("%s: adding calculated glue: %s",
                self, addendum)
            self.list.append(addendum)

        else:
            lineskip = self.doc[r'\lineskip'].value
            addendum = yex.box.Leader(
                    space = lineskip.space,
                    stretch = lineskip.stretch,
                    shrink = lineskip.shrink,
                    )
            logger.debug(r"%s: adding \lineskip: %s",
                self, addendum)
            self.list.append(addendum)

        self.doc[r'\prevdepth'] = item.depth

        super().append(item, tokens)

class Internal_Vertical(Vertical):
    is_inner = True

class Horizontal(Mode):
    is_horizontal = True
    our_type = yex.box.HBox

    def _handle_token(self, item, tokens):

        def append_space():
            font = tokens.doc['_font']

            interword_space = font[2]
            interword_stretch = font[3]
            interword_shrink = font[4]

            self.append(yex.box.Leader(
                    space = interword_space,
                    stretch = interword_stretch,
                    shrink = interword_shrink,
                    ))

        def append_character(ch):

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

            wordbox.append(ch)
            logger.debug(
                    "%s: added %s to wordbox: %s",
                    self, item, wordbox,
                    )

        if isinstance(item,
                (Letter, Other)
                ):

            if item.ch==' ':
                # This will be a space produced by a tie.
                # It's protected from being treated as a space until
                # it reaches here, so that the wordwrap routines
                # can't split it.
                append_space()
            else:
                append_character(item.ch)

        elif isinstance(item, (Superscript, Subscript)):

            raise yex.exception.ParseError(
                    f"You can't use {item} in {self}.",
                    )

        elif isinstance(item, Space):
            append_space()

        elif isinstance(item, Paragraph):

            if self.is_inner:
                return

            # FIXME: \unskip \penalty10000 \hskip\parfillskip

            # FIXME: linebreaks (see ch14)

            tokens.doc.end_group()

        else:
            raise ValueError(f"What do I do with token {item}?")

class Restricted_Horizontal(Horizontal):
    is_inner = True

class Math(Mode):
    is_math = True
    is_inner = True
    our_type = yex.box.HBox

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
