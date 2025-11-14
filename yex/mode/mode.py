import yex.box
import yex.value
import yex.parse
import yex.logging
from typing import Union, Self, Any, Type, Callable

logger = yex.logging.getLogger('mode')

class Mode:
    r"""
    A way of laying out boxes on a page. TeX defines three possible modes,
    each represented by a subclass of this class:
    `[Horizontal](yex.mode.Horizontal.md)`,
    `[Vertical](yex.mode.Vertical.md)`, and
    `[Math](yex.mode.Math.md)`.

    # What Modes do

    A [document](yex.Document.md)
    takes [tokens](yex.parse.Token.md) (and other items)
    from the [expander](yex.parse.Expander.md), and
    passes them to its current Mode. If these tokens are
    [controls](yex.control.Control.md) or otherwise magic,
    the Mode takes care of running them and handling their results.
    Otherwise, it stores them to its `list` attribute.

    # Where Modes live

    At the start of processing, a [document](yex.Document.md) creates
    an instance of the `Vertical` mode which lasts until processing is finished. This
    is always accessible at `doc.outermost_mode`, and initially at `doc.mode`.
    `doc['_mode']` is a slightly less efficient synonym.

    As processing continues, `doc.mode` may be replaced by other instances.
    One of the effects of ending a [group][yex.document.Group] is that it
    resets the mode to whatever it was when the group began.

    For example, when you begin a document, `doc.mode` is an instance of Vertical.
    When you start the first paragraph, `doc.mode` will be set
    to an instance of Horizontal. At the end of that paragraph, the Horizontal
    will be closed, and `doc.mode` will return to the original Vertical.

    # Inner Modes

    There are also subclasses which represent "inner" modes; these are
    embedded in "outer" modes as if they were words. `Horizontal` and `Vertical`
    are both "outer" in the general case, and have "inner" subclasses
    called `Restricted_Horizontal` and `Internal_Vertical`, respectively.

    `Math` is the other way about: it's "inner" in the general case,
    but has an "outer" subclass named `Display_Math`.

    Other than whether they're inner or outer, all these subclasses behave
    identically to their parents, except that `Inner_Vertical` can't send
    anything to the output drivers: that's reserved for `Vertical`
    itself.

    Because inner modes are embedded in other modes, their `recipient`
    can't be None.
    """

    is_horizontal:bool = False
    "Whether this is a horizontal mode."

    is_vertical:bool = False
    "Whether this is a vertical mode."

    is_math:bool = False
    "Whether this is a math mode."

    is_inner:bool = False
    "Whether this is an inner mode."

    _default_box_type: Type = None;

    def __init__(self,
                 doc: 'yex.Document',
                 to:Union[yex.value.Dimen, None] =None,
                 spread:Union[yex.value.Dimen, None] =None,
                 is_outermost:bool = False,
                 box_type:Union[Type, None] = None,
                 recipient:Union[Callable, None] = None,
                 ):
        r"""
        Args:
            is_outermost (bool): True if we're the outermost Mode.
                This implies that we're Vertical, we're not
                an inner mode, and we have no parent and no recipient.
          """

        self.doc = doc
        """
        The Document we belong to.
        """

        self.to = to
        r"""
        The width we've been asked to make our result,
        as requested by `\hbox to`.

        TeXbook:
            p77
        """

        self.box_type = box_type or self._default_box_type
        """
        The class of Box we're constructing.
        If this is None, we use a default which depends on
        the kind of mode we are. (For example, Horizontal
        produces an [HBox](yex.box.HVBox.md)).
        """

        self._result = None

        self.spread = spread
        r"""
        An amount to add to the natural width of our result,
        as requested by `\hbox spread`.

        TeXbook:
            p77
        """

        self.list: [Any] = []
        """
        The list of items we're building.
        """

        self.parent: Union[Self, None]
        """
        The Mode which was in charge before we took over.
        When we're done, it will be restored.
        The outermost Mode will have no parent.
        """
        if is_outermost:
            # The outermost mode has no parent; also, doc.mode won't
            # have been initialised yet
            self.parent = None
        else:
            self.parent = doc.mode

        self.recipient = None
        """
        When we're done with creating our list,
        we call `recipient` with a single argument, which is either
        a list of items or a single item. In any case, it will be
        called at most once. If you create a mode with no recipient,
        we supply a default which calls the `append()` method of
        its parent mode.
        """

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
    def name(self) -> str:
        """
        The name of this mode, in lowercase. For example, `"horizontal"`.
        """
        return self.__class__.__name__.lower()

    def close(self) -> None:
        """
        Tears down this Mode. Settles accounts with our recipient,
        and clears our list. After you call this method, it's safe
        to discard the Mode.

        Raises:
            yex.exception.ClosingOutermostError: if this mode is the
                outermost for its document, because outermost modes
                must persist throughout processing.
            yex.exception.UnexpectedOutermostModeError: if we find
                we've implausibly become the outermost mode.
            yex.exception.UnexpectedModeError: if we're not the
                current mode for our document.
        """

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

    def handle(self,
               item: Any,
               tokens: Union['yex.parse.Expander',None] = None,
            ):
        """
        Handles incoming items.

        TeXbook:
            p278

        Args:
            item: the incoming item to handle
            tokens: an Expander, for the use of the Control handlers
                we call.

        Raises:
            ValueError: if `item` is something so outlandish that
                we can't guess what to do with it.
        """

        self.doc.tracingcommands.notice_item(
                item=item,
                mode=self,
                )

        self._result = None

        if isinstance(item, yex.parse.BeginningGroup):
            logger.debug("%s: beginning a group", self)

            self.doc.begin_group(
                from_begingroup = False,
                )

        elif isinstance(item, yex.parse.EndGroup):
            logger.debug("%s: and ending a group", self)

            self.doc.end_group(
                    tokens=tokens,
                    from_endgroup = False,
                    )

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

    def run_single(self,
                   tokens: 'yex.parse.Expander',
                   ) -> None:
        r"""
        Reads a single piece of code from `tokens`.

        The code is delimited by `{` and `}` (or other chars which are
        set to those categories). Even so, the code isn't enclosed in
        a group: whatever it changes will stay changed.

        To do:
            This method isn't really about the mode any more.
            It should probably move to Expander.

        Args:
            tokens: the tokens to read and run.
        """
        token = tokens.next()

        if isinstance(token, yex.parse.BeginningGroup):
            tokens.push(token) # good
        else:
            raise yex.exception.NeededOpenCurlyBracketError(
                    problem = token,
                    )

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

    def showlist(self) -> None:
        r"""
        Prints our details to stdout, as part of the
        `\showlists` debugging command.

        TeXbook:
            p88
        """
        print(f"### {self}")

    def _switch_mode(self,
                     new_mode: Union[Self, str],
                     item: Any,
                     tokens: 'yex.parse.Expander',
            ) -> None:
        """
        Switches the current mode, and resubmits the item to the new mode.

        You should return immediately after calling this.

        Args:
            new_mode: the mode to switch to.
                This is simply submitted to `doc["_mode"]`, which see.
            item: the item we just read from `tokens`. It will
                be automatically submitted to the `handle()` method
                of the new mode.
            tokens: the token stream.
        """
        logger.debug("%s: %s: switching to %s",
                self, item, new_mode)

        self.doc['_mode'] = new_mode

        self.doc.mode.handle(item, tokens)

    def _handle_token(self,
                      item: Any,
                      tokens: 'yex.parse.Expander',
                      ):
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

    def append(self,
               item: Any,
               ) -> None:
        """
        Adds something to our list directly. You probably want to use
        `handle()` rather than this method.

        Args:
            item: what to add.
        """
        self.list.append(
                item,
                )
        logger.debug("%s: added %s to list",
                self, item,
                )

    def exercise_page_builder(self) -> None:
        """
        This is a no-op in every mode but Vertical, where it kicks off
        the output routine and clears our list.
        """
        pass

    def __getstate__(self) -> Any:
        # If we're being serialised, we're inside a Document.
        # The Document will save us as `doc['_mode']` but
        # also save our list as `doc['_mode_list']`.
        # So we don't need to serialise that here.
        return self.name
