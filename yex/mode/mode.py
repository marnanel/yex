import yex.box
import yex.value
import yex.parse
import logging

logger = logging.getLogger('yex.general')

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

    @property
    def result(self):
        return None

    def handle(self, item,
            tokens = None,
            ):
        """
        Handles incoming items. The rules are on p278 of the TeXbook.
        """

        if isinstance(item, yex.parse.BeginningGroup):
            logger.debug("%s: beginning a group", self)

            self.doc.begin_group()

        elif isinstance(item, yex.parse.EndGroup):
            logger.debug("%s: and ending a group", self)

            try:
                self.doc.end_group(tokens=tokens)
            except ValueError as ve:
                raise yex.exception.ParseError(
                        str(ve))

        elif isinstance(item, (yex.parse.Control, yex.parse.Active)):
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

        elif isinstance(item, yex.parse.Token):

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
