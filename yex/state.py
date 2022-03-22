# yex/state.py

r"`State` holds the state of a document while it's being processed."

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

commands_logger = logging.getLogger('yex.macros')
macros_logger = logging.getLogger('yex.macros')
restores_logger = logging.getLogger('yex.restores')

ASSIGNMENT_LOG_RECORD = "%s %-8s = %s"

KEYWORD_WITH_INDEX = re.compile(r'^([^;]+?);?(-?[0-9]+)$')

class State:
    r"""The state of a document while it's being processed.

    All macro definitions, fonts, and so on are kept here.

    Mostly, you interact with a State as if it was a dict, by getting
    and setting the values of its elements (known as "subscripting").
    This makes it clearer and easier when we have to reset values
    at the end of a TeX group.

    The names of all elements are strings. The values depend on the element.
    Some possible names:

        - The name of any predefined control word.
            For example, ``s['if']``. Don't include the backslash prefix.
        - The name of any user-defined macro.
        - The name of any register.
            For example, ``s['count23']`` or ``s['box12']``.
        - The prefix of any register, such as ``s['count']``
            You must supply `tokens`, so we can find the rest of it.
        - Some internal special values:
            - ``s['_font']``, for the current font.
            - ``s['_mode']``, for the current mode.
            - ``s['_output']``, for the current output driver.
        - A few controls can themselves be subscripted.
            Writing ``s['font3']`` is equivalent to writing
            ``s['font'][3]``.

            The second subscript must be an integer,
            and can be negative. You can also separate the field name
            from the field subscript with a semicolon. So
            ``s['font;3']``, ``s['font3']``, and ``s['font'][3]``
            are equivalant. ``s['cmr10;3']`` couldn't be written
            without the semicolon.

    Attributes:
        created_at (`datetime.datetime`): when the State was
            constructed. This provides initial values for
            TeX's time-based parameters, such as ``\year``.
        controls (:obj:`ControlsTable`): all the controls defined,
            both built-in and user-defined. Registers
            are stored in the ``registers`` attribute, not here.
            This may change ([#6](https://gitlab.com/marnanel/yex/-/issues/6)).
        registers (:obj:`RegisterTable`): the state of all the
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

        self.registers = yex.register.handlers(state=self)

        self.groups = []

        self.next_assignment_is_global = False
        self.parshape = None

        self.ifdepth = _Ifdepth_List([True])
        self.call_stack = []

        self.font = None
        self.mode = None
        self.output = None

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
                state = self,
                source = what,
                )
        e = yex.parse.Expander(
                t,
                **kwargs,
                )
        return e

    def __setitem__(self, field, value,
            from_restore = False):
        r"""Assigns a value to an element of this state.

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

        if field.startswith('_'):
            return self._setitem_internal(field, value, from_restore)

        if from_restore:
            restores_logger.info(
                    ASSIGNMENT_LOG_RECORD,
                    'R', field, repr(value))
        elif self.next_assignment_is_global:
            commands_logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    'G', field, repr(value))
            self.next_assignment_is_global = False
        else:
            commands_logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    '', field, repr(value))

            if self.groups:
                # XXX This is rather inefficient, because
                # we parse the fieldname twice
                previous = self.get(field, default=None)
                self.groups[-1].remember_restore(field,
                        previous)

        m = re.match(KEYWORD_WITH_INDEX, field)
        if m is not None:

            keyword, index = m.groups()

            for block in [self.registers, self.controls]:
                if keyword in block:
                    block[keyword][int(index)] = value
                    break
            return

        if field.startswith('_'):
            self.controls[field].value = value
        else:
            self.controls[field] = value

    def __getitem__(self, field,
            tokens=None,
            the_object_itself=True,
            ):
        r"""
        Retrieves the value of an element of this state.

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
            the_object_itself (`bool`): obsolete, and to be deleted soon
                ([#26](https://gitlab.com/marnanel/yex/-/issues/26)).

        Returns:
            the value you asked for

        Raises:
            `KeyError`: if there is no element with the name you requested.
            `ParseError`: if we attempted to complete the field name with
                `tokens`, but failed.
        """

        if field.startswith('_'):
            return self._getitem_internal(field, tokens)

        if the_object_itself:
            maybe_look_up = lambda x: x
            log_mark = 'TOI '
        else:
            maybe_look_up = lambda x: x.value
            log_mark = ''

        # If it's the name of a registers table (such as "count"),
        # and we have access to the tokeniser, read in the integer
        # which completes the name.
        #
        # Note that you can't subscript controls this way.
        # This is because you shouldn't access these from TeX code.
        if field in self.registers and tokens is not None:
            index = yex.value.Number(tokens).value
            result = self.registers[field][index]
            commands_logger.debug(r"  -- %s%s%d==%s",
                    log_mark, field, index, result)
            return maybe_look_up(result)

        # If it's in the controls table, that's easy.
        if field in self.controls:
            result = self.controls.__getitem__(
                    field,
                    the_object_itself=the_object_itself,
                    )
            commands_logger.debug(r"  -- %s%s==%s",
                    log_mark, field, result)
            return result

        # Or maybe it's already a variable name plus an integer.
        m = re.match(KEYWORD_WITH_INDEX, field)

        if m is not None:
            keyword, index = m.groups()

            for block in (self.registers, self.controls):
                try:
                    result = block[keyword][int(index)]
                    commands_logger.debug(r"  -- %s%s==%s",
                            log_mark, field, result)
                    return maybe_look_up(result)
                except KeyError:
                    pass

        raise KeyError(field)

    def get(self, field, default=None,
            the_object_itself=True,
            tokens=None):
        r"""
        Retrieves the value of an element of this state.

        Just like `__getitem__`, except that we return `None` if
        the lookup fails.

        Args:
            `default`: what to return if there is no such element.
                Otherwise, as for `__getitem__`.
        """
        try:
            return self.__getitem__(field,
                    tokens=tokens,
                    the_object_itself=the_object_itself,
                    )
        except KeyError:
            return default

    def _setitem_internal(self, field, value, from_restore):
        if field=='_font':
            self.font = yex.font.Font(
                    filename=value,
                    )
        elif field=='_mode':
            if isinstance(value, yex.mode.Mode):
                self.mode = value
            elif value is None:
                self.value = None
            else:
                try:
                    self.mode = self.mode_handlers[str(value)](self)
                except KeyError:
                    raise ValueError(f"no such mode: {value}")
        elif field=='_output':
            if isinstance(value, yex.output.Output):
                self.output = value
            elif value is None:
                self.value = None
            else:
                try:
                    self.mode = self.mode_handlers[str(value)](
                            filename=None, # TODO
                            )
                except KeyError:
                    raise ValueError(f"no such output: {value}")
        else:
            raise KeyError(field)

    def _getitem_internal(self, field, tokens):
        if field=='_font':
            if self.font is None:
                self.font = yex.font.Font(
                        filename='cmr10.tfm',
                        )
                commands_logger.debug(
                        "created Font on first request: %s",
                        self.font)
            return self.font

            pass
        elif field=='_mode':
            if self.mode is None:
                self.mode = yex.mode.Vertical(state=self)
                commands_logger.debug(
                        "created Mode on first request: %s",
                        self.mode)
            return self.mode
        elif field=='_output':
            if self.output is None:
                self.output = yex.output.get_default()(
                        state=self,
                        filename=None, # TODO
                        )
                commands_logger.debug(
                        "created Output on first request: %s",
                        self.output)
            return self.output
        else:
            raise KeyError(field)

    def begin_group(self):
        r"""
        Opens a new group. Called by ``{`` and ``\begingroup``.

        Args:
            none

        Returns:
            `None`
        """
        new_group = Group(
                state = self,
                )
        self.groups.append(new_group)
        commands_logger.debug("%s[[ Started group: %s",
                '  '*len(self.groups),
                self.groups)

    def end_group(self):
        r"""
        Closes a group. Discards all settings made since the most recent
        `begin_group`, other than global settings.
        Called by ``}`` and ``\endgroup``.

        Args:
            none

        Returns:
            `None`
        Returns:
            none
        """
        if not self.groups:
            raise yex.exception.YexError("More groups ended than began!")

        commands_logger.debug("%s]] Ended group: %s",
                '  '*len(self.groups),
                self.groups)
        ended = self.groups.pop()
        ended.run_restores()

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

class Group:
    r"""
    A group, in the TeX sense.

    Created by ``{`` or ``\begingroup``, and ended by
    ``}`` or ``\endgroup``.  When the group ends, all assignments
    (except global assignments) will be undone

    Attributes:
        state (`State`): the state we're in
        restores (dict mapping `str` to arbitrary types): element values to
            restore when the group ends.
    """
    def __init__(self, state):
        self.state = state
        self.restores = {}

    def remember_restore(self, f, v):
        """
        Stores `f` and `v` so we can do ``self.state[f]=v`` later.

        If multiple assignments are made to the same element in the
        same group, we only record the first: that's all we need to know to
        restore the value, and the others will be inaccurate anyway.

        Ignores ``f="inputlineno"``, since attempting to restore the
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
        if f in ('inputlineno', ):
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
        restores_logger.debug("Beginning restores: %s",
                self.restores)
        self.next_assignment_is_global = False
        for f, v in self.restores.items():
            self.state.__setitem__(
                    field = f,
                    value = v,
                    from_restore = True,
                    )

        restores_logger.debug("  -- restores done.")
        self.restores = {}

    def __repr__(self):
        return 'g%04x' % (hash(self) % 0xffff,)

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
    Stored in the list State.call_stack.

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
            ''.join([c.ch for c in v])
            for (f,v) in sorted(self.args.items())])
        return f'{self.callee}({args}):{self.location}'
