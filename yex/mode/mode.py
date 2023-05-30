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

    def __init__(self, doc,
            to=None, spread=None,
            is_outermost=False,
            box_type=None,
            recipient=None,
            ):

        self.doc = doc
        self.to = to
        self.spread = spread
        self.list = []
        self.box_type = box_type or self.default_box_type
        self._result = None

        if is_outermost:
            # The outermost mode has no parent; also, doc.mode won't
            # have been initialised yet
            self.parent = None
        else:
            self.parent = doc.mode

        if recipient is not None:
            self.recipient = recipient
        elif self.is_inner:
            raise ValueError("inner modes must specify a recipient")
        elif is_outermost:
            self.recipient = None
        else:
            def pass_up(result):
                logger.debug("   -- result was %s", result)

                logger.debug("   -- passing to previous mode, %s", self.parent)

                if isinstance(result, list):
                    for item in result:
                        self.parent.append(item=item)
                else:
                    self.parent.append(item=result)

            self.recipient = pass_up

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def close(self):

        if self.doc.outermost_mode==self:
            raise yex.exception.ClosingOutermostModeError()

        self.recipient(self._calculate_result())
        self.list = None
        # FIXME:for Horizontal: \unskip \penalty10000 \hskip\parfillskip

        if self.doc.mode==self:
            if self.doc.outermost_mode==self:
                raise yex.exception.UnexpectedOutermostError(
                        mode = self,
                        )
            self.doc.mode = self.parent
        else:
            raise UnexpectedModeError(
                    expected = self,
                    found = self.doc.mode,
                    )

        logger.debug('%s: closed; doc.mode==%s', self, self.doc.mode)

    def _calculate_result(self):
        return self.box_type.from_contents(
                contents=self.list,
                to=self.to,
                spread=self.spread,
                )

    def handle(self, item,
            tokens = None,
            ):
        """
        Handles incoming items. The rules are on p278 of the TeXbook.
        """

        self._result = None

        if isinstance(item, yex.parse.BeginningGroup):
            logger.debug("%s: beginning a group", self)

            self.doc.begin_group(
                from_begingroup = False,
                )

        elif isinstance(item, yex.parse.EndGroup):
            logger.debug("%s: and ending a group", self)

            try:
                self.doc.end_group(
                        tokens=tokens,
                        from_endgroup = False,
                        )
            except ValueError as ve:
                raise yex.exception.ParseError(
                        str(ve))

        elif isinstance(item, (yex.parse.Control, yex.parse.Active)):
            handler = self.doc.get(
                    field=item.identifier,
                    default=None)

            logger.debug("%s: %s: handler is %s",
                    self, item, handler
                    )

            if handler is not None:
                handler(tokens = tokens)
            else:
                logger.debug("%s:    -- writing the name instead", self)
                for c in item.identifier:
                    self._handle_token(
                            yex.parse.Other(ch=c),
                            tokens=tokens,
                            )


        elif isinstance(item, yex.parse.Token):

            # any other kind of token

            self._handle_token(item, tokens)

        elif isinstance(item, yex.control.Control):

            item(tokens = tokens)

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
        r"""
        Reads a single piece of code from `tokens`.

        The code is delimited by `{` and `}` (or other chars which are
        set to those categories). Even so, the code isn't enclosed in
        a group: whatever it changes will stay changed.

        Args:
            tokens (`Expander`): the tokens to read and run.

        Returns:
            None.
        """
        # FIXME This method isn't really about the mode any more.
        # It should probably move to Expander.

        token = tokens.next()

        if isinstance(token, yex.parse.BeginningGroup):
            tokens.push(token) # good
        else:
            raise yex.exception.YexError(
                    f"{self.name} must be followed by "
                    "'{' "
                    f"(not {token})")

        logger.debug("%s: run_single: gathering the tokens",
                self,
                )
        for token in tokens.another(
                on_eof='exhaust',
                level='executing',
                bounded='single',
                ):

            tokens.doc.mode.handle(
                        item=token,
                        tokens=tokens,
                        )

        logger.debug("%s: run_single:   -- done",
                self,
                )

    def showlist(self):
        r"""
        Shows our details, as part of the
        \showlists debugging command.
        See p88 of the TeXbook.
        """
        print(f"### {self}")

    def _switch_mode(self, new_mode, item, tokens,
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
        """
        logger.debug("%s: %s: switching to %s",
                self, item, new_mode)

        self.doc['_mode'] = new_mode

        self.doc.mode.handle(item, tokens)

    def _handle_token(self, item, tokens):
        raise NotImplementedError()

    def __repr__(self):

        repr_name = self.name.replace('_', ' ')

        if self.doc.outermost_mode==self:
            repr_name += ';outermost'

        repr_id = '%04x' % (id(self) % 0xFFFF)
        if self.list is None:
            repr_list = '<none>'
        else:
            try:
                repr_list = yex.box.Box.list_to_symbols_for_repr(self.list)

                if repr_list=='':
                    repr_list = '<empty>'
            except AttributeError:
                repr_list = '<inchoate>'

        return f'[{repr_name};{repr_id};{repr_list}]'

    def append(self, item):
        self.list.append(
                item,
                )
        logger.debug("%s: added %s to list",
                self, item,
                )

    def exercise_page_builder(self):
        # this is a no-op in every mode but Vertical
        pass

    def __getstate__(self):
        # If we're being serialised, we're inside a Document.
        # The Document will save us as `doc['_mode']` but
        # also save our list as `doc['_mode_list']`.
        # So we don't need to serialise that here.
        return self.name
