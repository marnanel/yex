# yex.document.py

r"`Document` holds a document while it's being processed."

import datetime
import yex.value
import yex.box
import yex.control
import yex.register
import yex.mode
import yex.exception
import yex.parse
import re
import logging

logger = logging.getLogger('yex.general')
restores_logger = logging.getLogger('yex.restores')

ASSIGNMENT_LOG_RECORD = "%s %-8s = %s"

KEYWORD_WITH_INDEX = re.compile(r'^([^;]+?);?(-?[0-9]+)$')

INTERNAL_FIELDS = ['_mode', '_font', '_target']

def REGISTER_NAME(n):
    """
    Temporary: removes leading backslashes to turn control names into
    register names. When issue 6 is resolved, this won't be needed.
    """
    if n.startswith('\\'):
        return n[1:]
    else:
        return n

class Document:
    r"""A document, while it's being processed.

    All macro definitions, fonts, and so on are kept here.

    Mostly, you interact with a Document as if it was a dict, by getting
    and setting the values of its elements (known as "subscripting").
    This makes it clearer and easier when we have to reset values
    at the end of a TeX group.

    The names of all elements are strings. The values depend on the element.
    Some possible names:

        - The name of any predefined control.
            For example, ``doc['\if']``. Don't include the backslash prefix.
        - The name of any user-defined macro.
        - The name of any register.
            For example, ``doc['\count23']`` or ``doc['\box12']``.
        - The prefix of any register, such as ``doc['\count']``
            You must supply `tokens`, so we can find the rest of it.
        - Some internal special values:
            - ``doc['_font']``, for the current font.
            - ``doc['_mode']``, for the current mode.
        - A few controls can themselves be subscripted.
            Writing ``doc['\font3']`` is equivalent to writing
            ``doc['\font'][3]``.

            The second subscript must be an integer,
            and can be negative. You can also separate the field name
            from the field subscript with a semicolon. So
            ``doc['font;3']``, ``doc['font3']``, and ``doc['font'][3]``
            are equivalant. ``doc['cmr10;3']`` couldn't be written
            without the semicolon.

    Attributes:
        created_at (`datetime.datetime`): when the Document was
            constructed. This provides initial values for
            TeX's time-based parameters, such as ``\year``.
        controls (:obj:`ControlsTable`): all the controls defined,
            both built-in and user-defined. Registers
            are stored in the ``registers`` attribute, not here.
            This may change ([#6](https://gitlab.com/marnanel/yex/-/issues/6)).
        registers (:obj:`RegisterTable`): the doc of all the
            registers, such as ``\count12``.
        groups (list of :obj:`Group`): the nested groups
            of the TeX source being processed, which are
            created either by ``{``/``}`` or by
            ``\begingroup``/``\endgroup``.
        fonts (dict of :obj:`Font`): fonts currently loaded.
            They need not have identifiers in the controls
            table, but they're not accessible from TeX code
            unless they do.
        font (:obj:`Font`): the currently selected font.
        mode (:obj:`Mode`): the currently selected mode.
        target (any or `None`): at the end of certain modes, we
            call this object with `tokens=tokens` and `item=v`,
            where `v` is the `result` property of the mode;
            if this is `None`, the mode will push `v` instead
        output (:obj:`Output`): the output driver. For example,
            the PDF driver or the SVG driver.
        next_assignment_is_global (bool): if True, the next
            use of `__setitem__` will apply until further notice.
            Otherwise, it applies until the end of the
            current group.
        parshape (list of :obj:`Dimen`): you probably don't
            need to look at this. It's a list of constraints on lengths
            of lines in the current paragraph, set by ``\parshape``
            but kept here so it persists.
        ifdepth (`_Ifdepth_List`): essentially a list of booleans,
            representing whether particular conditional clauses are
            executing. For example, after ``\iftrue`` the top member
            will be True, after ``\iffalse`` it will be False, and
            ``\else`` will (generally) negate the top member.
    """


    mode_handlers = yex.mode.handlers()

    def __init__(self):

        self.created_at = datetime.datetime.now()

        self.controls = yex.control.ControlsTable()
        self.controls |= yex.control.handlers()

        self.fonts = {}

        self.registers = yex.register.handlers(doc=self)

        self.groups = []

        self.next_assignment_is_global = False
        self.parshape = None

        self.ifdepth = _Ifdepth_List([True])
        self.call_stack = []
        self.hungry = []

        self.font = None
        self.mode = None
        self.target = None

        self.mode_stack = []
        self.output = []

    def open(self, what,
            **kwargs):

        r"""Opens a string, a list of characters, or a file for reading.

            Constructs a :obj:`Tokeniser` on `what`,
            and an :obj:`Expander` on that `Tokeniser`.
            Returns the `Expander`.

            Args:
                what (`str`, `list`, or file-like): where we're getting the
                    symbols from.
                **kwargs: Arguments to pass to the `Expander`.

            Returns:
                An :obj:`Expander`.
            """
        t = yex.parse.Tokeniser(
                doc = self,
                source = what,
                )
        e = yex.parse.Expander(
                t,
                **kwargs,
                )
        return e

    def read(self, what,
            **kwargs):
        r"""Reads a string, or a file, and adds it to this Document.

            Args:
                thing (`str`, or file-like): something to read characters from.
                **kwargs: Arguments to pass to the `Expander` which we'll
                    use to parse the input.

            Returns:
                `None`
        """

        logger.debug("%s: reading from %s", self, what)
        logger.debug("%s: reading with params %s", self, kwargs)

        e = self.open(what, **kwargs)

        logger.debug("%s: reading through %s", self, e)

        for item in e:
            logger.debug("  -- resulting in: %s", item)

            if item is None:
                break

            self['_mode'].handle(
                    item=item,
                    tokens=e,
                    )

        logger.debug("%s: done", self)

    def __iadd__(self, thing):
        r"""Short for `read(thing)`. See `read` for more information.

            Args:
                thing (`str`, or file-like): something to read characters from.

            Returns:
                self (`Document`)
        """
        self.read(thing)

        return self

    def __setitem__(self, field, value,
            from_restore = False):
        r"""Assigns a value to an element of this doc.

            Args:
                field (`str`): the name of the element to change.
                    See the class description for a list of field names.
                value (any): the value to give the element.
                    Acceptable types and values depend on the field name.
                from_restore (`bool`): if True, we're in the process of
                    restoring settings at the end of a group; otherwise,
                    we're not, and we store a record of this assignment
                    until we are. You probably don't need to use this.

            Raises:
                `KeyError`: if the field doesn't name an element
                `TypeError`: if the value has the wrong type for the field
                `ValueError`: if there's something wrong with the value
                and many other possibilities, depending on which element it is

            Returns:
                `None`
            """

        if from_restore:
            restores_logger.info(
                    "{restoring %s=%s}",
                    field, repr(value))
            logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    'R', field, repr(value))
        elif self.next_assignment_is_global:
            logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    'G', field, repr(value))
            self.next_assignment_is_global = False
        else:
            logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    '', field, repr(value))

            if self.groups:
                # XXX This is rather inefficient, because
                # we parse the fieldname twice
                previous = self.get(field, default=None)
                self.groups[-1].remember_restore(field,
                        previous)

        if field in INTERNAL_FIELDS:
            # Special-cased for now. Eventually we should have parameters
            # which just set and get the relevant fields in Document,
            # but atm there's no handle to Document (or the tokeniser)
            # passed into parameters when we read them.
            return self._setitem_internal(field, value, from_restore)

        m = re.match(KEYWORD_WITH_INDEX, field)

        if m is None:

            # Must be a control, rather than a register.
            self.controls[field] = value

        else:
            keyword, index = m.groups()

            if REGISTER_NAME(keyword) in self.registers:
                self.registers[REGISTER_NAME(keyword)][int(index)] = value
            elif keyword in self.controls:
                self.controls[keyword][int(index)] = value
            else:
                # Check for missing leading backslashes.
                # This should only be a problem in legacy code,
                # so we can take this check out again in a few weeks.
                # (March 2022)
                if field[0]!='\\':
                    try:
                        self.__setitem__('\\'+field, value)
                        raise ValueError(
                                f"lookup of {field} failed, when "
                                rf"\{field} would have worked; "
                                "this is almost certainly a mistake"
                                )
                    except KeyError:
                        pass

                raise KeyError(field)

    def get(self, field,
            tokens=None,
            **kwargs,
            ):
        r"""
        Retrieves the value of an element of this doc.

        Args:
            field (`str`): the name of the element to find.
                See the class description for a list of field names.
            tokens (`Expander`): in some cases, `field` may only be a
                prefix of a proper element name. For example, the count
                register numbered 23 is named "count23", but this name
                is three tokens if you write it in TeX: ``\count``, ``2``,
                and ``3``. The lookup will only fetch ``\count``, which
                isn't in itself the name of an element. So, in such cases
                we fetch the next tokens to find the full name.
            default (any): what to return if there is no such element.
                If this is not specified, we raise `KeyError`.

        Returns:
            the value you asked for

        Raises:
            `KeyError`: if there is no element with the name you requested,
                and `default` was not specified.
            `ParseError`: if we attempted to complete the field name with
                `tokens`, but failed.
        """

        if field in INTERNAL_FIELDS:
            return self._getitem_internal(field, tokens)

        if [k for k in kwargs.keys() if k!='default']:
            raise TypeError(f"unknown argument {k}")

        # If it's the name of a registers table (such as "count"),
        # and we have access to the tokeniser, read in the integer
        # which completes the name.
        #
        # Note that you can't subscript controls this way.
        # This is because you shouldn't access these from TeX code.
        if REGISTER_NAME(field) in self.registers and tokens is not None:
            index = yex.value.Number(tokens).value
            result = self.registers[REGISTER_NAME(field)][index]
            logger.debug(r"  -- %s%d==%s",
                    field, index, result)
            return result

        # If it's in the controls table, that's easy.
        if field in self.controls:
            result = self.controls.__getitem__(
                    field,
                    )
            logger.debug(r"  -- %s==%s",
                    field, result)
            return result

        # Or maybe it's already a variable name plus an integer.
        m = re.match(KEYWORD_WITH_INDEX, field)

        if m is not None:
            keyword, index = m.groups()

            try:
                result = self.registers[REGISTER_NAME(keyword)][int(index)]
                logger.debug(r"  -- %s==%s",
                        field, result)
                return result
            except KeyError:
                pass

            try:
                result = self.controls[keyword][int(index)]
                logger.debug(r"  -- %s==%s",
                        field, result)
                return result
            except KeyError:
                pass

        # Check for missing leading backslashes.
        # This should only be a problem in legacy code,
        # so we can take this check out again in a few weeks.
        # (March 2022)
        if field[0]!='\\':
            try:
                self.__getitem__('\\'+field)
                raise ValueError(
                        f"lookup of {field} failed, when "
                        rf"\{field} would have worked; "
                        "this is almost certainly a mistake"
                        )
            except KeyError:
                pass

        if 'default' in kwargs:
            return kwargs['default']
        else:
            raise KeyError(field)

    def __getitem__(self, field):
        return self.get(field)

    def _setitem_internal(self, field, value, from_restore):
        if field=='_font':

            # TODO test: do we remember restore?

            if isinstance(value, str):
                value = yex.font.Font(
                        filename=value,
                        )

        elif field=='_mode':

            if not hasattr(value, 'handle'):
                # okay, maybe it's the name of a mode
                try:
                    handler = self.mode_handlers[str(value)]
                except KeyError:
                    raise ValueError(f"no such mode: {value}")
                value = handler(self)

        self.__setattr__(field[1:], value)

    def _getitem_internal(self, field, tokens):
        if field=='_font':
            if self.font is None:
                self.font = yex.font.get_font_from_name(
                        name=None,
                        doc=self,
                        )
                logger.debug(
                        "created Font on first request: %s",
                        self.font)

        elif field=='_mode':
            if self.mode is None:
                self.mode = yex.mode.Vertical(doc=self)
                logger.debug(
                        "created Mode on first request: %s",
                        self.mode)

        return getattr(self, field[1:])

    def begin_group(self,
            flavour=None,
            ephemeral=False,
            ):
        r"""
        Opens a new group.

        Called by ``{`` and ``\begingroup``.

        Args:
            flavour (`str` or `None`): if `None`, create ordinary group;
                if `"no-mode"` create group which won't restore a mode
                (this is for `\begingroup`; not yet implemented);
                if `"only-mode"` create a group which will only restore a mode.
                Otherwise, raise `ValueError`.
            ephemeral (`bool`): if this is True, then when this group closes
                it will automatically close the next group down (and so on).
                Defaults to False.

        Raises:
            `ValueError`: if flavour is other than the options given above.

        Returns:
            `Group`. This is mainly useful to pass to `end_group()` to make
            sure the groups are balanced.
        """

        if flavour is None:
            new_group = Group(
                    doc = self,
                    ephemeral = ephemeral,
                    )
        elif flavour=='only-mode':
            try:
                delegate = self.groups[-1]
            except IndexError:
                delegate = None

            new_group = GroupOnlyForModes(
                    doc = self,
                    delegate = delegate,
                    ephemeral = ephemeral,
                    )
        else:
            raise ValueError(flavour)

        self.groups.append(new_group)
        logger.debug("%s: Started group: %s",
                '  '*len(self.groups),
                self.groups)

        return new_group

    def end_group(self,
            group=None,
            tokens=None,
            ):
        r"""
        Closes a group.

        Discards all settings made since the most recent `begin_group()`,
        except:
            - global settings
            - `'_mode'`, if flavour is `'no-mode'`
            - anything but `'mode'`, if flavour is `'only-mode'`.

        Called by ``}`` and ``\endgroup``.

        Args:
            group (`Group` or `None`): the group we should be closing.
                This only functions as a check; we can only close the
                top group in the stack. If this is None, which is the
                default, we just close the top group without doing a check.
                If for some reason we have to close multiple groups,
                this check is not carried out on ephemeral groups.

            tokens (`Expander` or `None`): the token stream we're reading.
                This is only needed if the group we're ending has produced
                a list which now has to be handled.

                This argument *can* be `None`, if you're sure that won't
                happen; if it does, and the handler needs a token stream,
                you'll get an error from the handler.

        Raises:
            `YexError`: if there are no groups remaining.

        Returns:
            `None`
        """
        if not self.groups:
            raise yex.exception.YexError("More groups ended than began!")

        while True:
            logger.debug("%s]] Ended group: %s",
                    '  '*len(self.groups),
                    self.groups)
            ended = self.groups.pop()

            if group is not None and not ended.ephemeral:
                if ended is not group:
                    raise ValueError(
                            f"expected to close group {group}, "
                            f"but found group {ended}."
                            )
                group = None

            if '_mode' in ended.restores:

                mode_result = self.mode.result

                if self.target is None:
                    if mode_result is not None:
                        logger.debug("%s: ended mode %s; "
                                "doc['_target'] "
                                "is None; pushing value: %s; "
                                "try not to make a habit of that",
                                self, self.mode, mode_result)

                        tokens.push(mode_result)

                else:

                    logger.debug("%s: ended mode %s; handling %s(%s)",
                            self, self.mode, self.target, mode_result)

                    self.target(tokens=tokens, item=mode_result)

                self.mode.list = None

            ended.run_restores()

            if ended.ephemeral and self.groups:
                logger.debug("  -- the group was ephemeral, so loop")
            else:
                break

    def showlists(self):
        r"""
        Prints details of the list in the current `Mode`, and of all
        the containers it contains, and all the containers *they* contain,
        and so on.

        Implements the `\showlists` debugging command:
        see p88 of the TeXbook.

        Currently disabled.

        Args:
            none

        Returns:
            `None`
        """
        raise NotYetImplemented()

    def __len__(self):
        r"""
        Finds the number of groups currently open, plus 1.
        (If there are no groups currently open, that works pretty
        much like a group for most purposes.)

        Returns:
            The number of groups, plus 1.
        """
        return len(self.groups)+1

    def remember_restore(self, f, v):
        r"""
        Stores a record of an assignment, so it can be undone at the end
        of the current group. Doesn't actually make the assignment.
        You probably don't want to use this.

        Other than changes to internal flags, this just calls through
        to `remember_restore` in the topmost :obj:`Group`.

        Args:
            f: field name
            v: field value

        Returns:
            `None`
        """
        if not self.groups:
            return
        if self.next_assignment_is_global:
            self.next_assignment_is_global = False
            return
        self.groups[-1].remember_restore(f,v)

    def shipout(self, box):
        """
        Sends a box, or multiple boxes, to the output queue.

        Anything passed to this method will be stored, rather than
        rendered immediately. It will be rendered when the `save` method
        is called.

        Args:
            box (`Box`, or list of `Box`): a box or boxes to be rendered.

        Returns:
            `None`
        """
        if isinstance(box, list):
            self.output.extend(box)
        else:
            self.output.append(box)

    def end_all_groups(self,
            tokens = None,
            ):
        """
        Closes all open groups.

        Args:
            tokens (`Expander` or `None`): the token stream we're reading.
                This is only needed if one of the groups we're ending
                has produced a list which now has to be handled.

        Returns:
            `None`.
        """
        logger.debug("%s: ending all groups: %s", self,
                self.groups)
        while self.groups:
            self.end_group(
                    tokens=tokens,
                    )
        logger.debug("%s:   -- done ending all groups",
                self)

    def save(self, filename, driver):
        """
        Renders the document.

        Ends all open groups before it attempts to render.

        Args:
            filename (`str`): the name of the file to write to.
            driver: (`yex.Output`): the output driver.

        Raises:
            OSError: if something goes wrong during writing

        Returns:
            `None`
        """

        logger.debug("%s: saving document", self)
        self.end_all_groups()

        if not self.output:
            logger.debug("%s:   -- but there was no output", self)
            print("note: there was no output")
            return

        logger.debug("%s:   -- saving to %s",
                self, filename)
        logger.debug("%s:   -- using %s",
                self, driver)
        driver.render(self.output)
        logger.debug("%s:   -- done!", self)

    def __repr__(self):
        return '[doc;boxes=%d]' % (len(self.output))

class Group:
    r"""
    A group, in the TeX sense.

    Created by ``{`` or ``\begingroup``, and ended by
    ``}`` or ``\endgroup``.  When the group ends, all assignments
    (except global assignments) will be undone.

    Attributes:
        doc (`Document`): the doc we're in
        restores (dict mapping `str` to arbitrary types): element values to
            restore when the group ends.
        ephemeral (`bool`): `True` if this group should end as soon as
            the first group inside it.
    """

    def __init__(self, doc, ephemeral=False):
        self.doc = doc
        self.restores = {}
        self.ephemeral = ephemeral

    def remember_restore(self, f, v):
        r"""
        Stores `f` and `v` so we can do ``self.doc[f]=v`` later.

        If multiple assignments are made to the same element in the
        same group, we only record the first: that's all we need to know to
        restore the value, and the others will be inaccurate anyway.

        Ignores ``f="\inputlineno"``, since attempting to restore the
        previous line number would give unexpected results.

        This method is not called "record_restore" because people might
        interpret "record" as a noun.

        Args:
            f (`str`): the fieldname of the element
            v (arbitrary): the value the element had before the assignment

        Raises:
            None.

        Returns:
            `None`
        """
        if f in (r'\inputlineno', ):
            # that makes no sense
            return

        if f in self.restores:
            restores_logger.debug(
                    "Redefinition of %s; ignored for remembers", f)
            return

        try:
            v = v.value
        except AttributeError:
            pass

        restores_logger.debug(
                ASSIGNMENT_LOG_RECORD,
                '*', f, repr(v))
        self.restores[f] = v

    def run_restores(self):
        """
        Carries out each restore recorded by `remember_restore`.

        The restores happen in no particular order.

        Raises:
            None.

        Returns:
            `None`
        """
        restores_logger.debug("%s: beginning restores: %s",
                self, self.restores)

        self.next_assignment_is_global = False
        for f, v in self.restores.items():
            self.doc.__setitem__(
                    field = f,
                    value = v,
                    from_restore = True,
                    )

        restores_logger.debug("%s:  -- restores done.",
                self)
        self.restores = {}

    def __repr__(self):
        if self.ephemeral:
            e = ';e'
        else:
            e = ''

        return 'g;%04x%s' % (hash(self) % 0xffff, e)

class GroupOnlyForModes(Group):
    r"""
    Like Group, except it only restores `'_mode'` and `'_target'`.

    All other changes are passed on to a delegate Group, which is
    the one previous to this Group in the groups list.

    This is for mode changes when we know we'll need to snap back
    to the previous mode.

    Attributes:
        doc (`Document`): the doc we're in
        delegate (`Group`): a Group which can handle changes that we can't.
            May be `None`, in which case such changes are ignored.
    """

    FIELDS = set(['_mode', '_target'])

    def __init__(self, doc, delegate, ephemeral):
        super().__init__(doc, ephemeral)
        self.delegate = delegate
        restores_logger.debug('Will restore _mode and _target.')

    def remember_restore(self, f, v):
        if f in self.FIELDS:
            super().remember_restore(f, v)
        elif self.delegate is not None:
            self.delegate.remember_restore(f, v)

    def __repr__(self):
        return super().__repr__()+';ofm'

class _Ifdepth_List(list):
    """
    Just like an ordinary list, except that its representation
    is suited for printing a list of booleans compactly.
    """
    def __repr__(self):
        def _repr(v):
            if v==True:
                return 'T'
            elif v==False:
                return 'f'
            else:
                return repr(v)
        result = ''.join([_repr(v) for v in self])
        return result

class Callframe:
    """
    Description of a macro call.

    Only used for tracebacks; the macros take care of themselves.
    Stored in the list Document.call_stack.

    Attributes:
        callee (`Token`): the name of the macro that made the call.
        args (list of lists of `Token`): the arguments to the call.
        location (`yex.parse.source.Location`): where the call was made
            (as a named tuple of filename, line, and column).
    """
    def __init__(self,
            callee,
            args,
            location,
            ):
        self.callee = callee
        self.args = args
        self.location = location

    def __repr__(self):
        args = ','.join([
            ''.join([str(c) for c in v])
            for (f,v) in sorted(self.args.items())])
        return f'{self.callee}({args}):{self.location}'

    def jump_back(self, tokens):
        logger.debug("%s: jumping back", self)
        tokens.location = self.location
