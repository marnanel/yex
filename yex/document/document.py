r"`Document` holds a document while it's being processed."

import datetime
import yex
import yex.decorator
import yex.box
import re
import functools
from yex.document.callframe import Callframe
from yex.document.group import Group, GroupOnlyForModes, ASSIGNMENT_LOG_RECORD
import logging

logger = logging.getLogger('yex.general')

KEYWORD_WITH_INDEX = re.compile(r'^([^;]+?);?(-?[0-9]+)$')

FORMAT_VERSION = 1

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
            both built-in and user-defined.
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
        contents (list of :obj:`Box`): the rendered contents
            waiting to go to the output driver.
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


    def __init__(self):

        self.created_at = datetime.datetime.now()

        self.controls = yex.control.ControlsTable(doc=self)
        self.controls |= yex.control.handlers()

        self.fonts = {}

        self.groups = []

        self.next_assignment_is_global = False
        self.parshape = None

        self.ifdepth = _Ifdepth_List([True])
        self.call_stack = []

        self.font = None
        self.mode = None

        self.mode_stack = []
        self.output = None
        self.contents = []

        self.controls |= {
                '_inputs': yex.io.StreamsTable(doc=self,
                our_type=yex.io.InputStream),
                '_outputs': yex.io.StreamsTable(doc=self,
                our_type=yex.io.OutputStream),
                }

    def open(self, what,
            **kwargs):

        r"""Opens a string, a list of characters, or a file for reading.

            Constructs a :obj:`Expander` on `what`.

            Args:
                what (`str`, `list`, or file-like): where we're getting the
                    symbols from.
                **kwargs: Arguments to pass to the `Expander`.

            Returns:
                An :obj:`Expander`.
            """
        e = yex.parse.Expander(
                what,
                doc = self,
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

            self.mode.handle(
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
            index = None,
            param_control = False,
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
            logger.debug(
                    "{restoring %s=%s}",
                    field, repr(value))
            logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    'R', field, repr(value))
        elif self.next_assignment_is_global:
            logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    'G', field, repr(value))
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

        logger.debug("%s[%s], index=%s, global=%s: setting value to %s",
                self, repr(field), index, self.next_assignment_is_global,
                value)

        self.next_assignment_is_global = False

        item, index = self._find_control_and_index(
                field = field,
                index = index,
                )

        if item is not None and index is not None:

            index = int(index)

            logger.debug("doc[%s]=%s: setting %s member %s",
                    repr(field), repr(value),
                    item, index,
                    )
            item.get_element(index=index).value=value

        elif param_control or item is None or not item.is_queryable:

            logger.debug("doc[%s]=%s: setting control",
                    repr(field), repr(value))
            self.controls[field] = value

        else:

            logger.debug("doc[%s]=%s: setting %s.value",
                    repr(field), repr(value),
                    item,
                    )
            item.value = value

    def __getitem__(self, field,
            index=None,
            param_control=False,
            **kwargs,
            ):
        r"""
        Retrieves the value of an element of this doc.

        Also called get().

        doc['...'] is equivalent to calling get() with the default arguments.

        In some cases, `field` may refer to an array. For example,
        the count register numbered 23 is named "\count23", but this name
        is three tokens if you write it in TeX: ``\count``, ``2``, and ``3``.
        Array indexes are always integers.

        There are several ways to retrieve the value of \count23
        using this method:

            * get(field=r'\count23')
            * get(field=r'\count', index=23)
            * get(field=r'\count', tokens=some_expander)

        In the last case, we scan the next few characters of the Expander
        to find an integer.

        Args:
            field (`str`): the name of the element to find.
                See the class description for a list of field names.
            index (int): if "field" refers to an array, this can be
                an index into it; if it isn't, this should be None
            tokens (`Expander`): used to find indexes for an array; see above
            default (any): what to return if there is no such element.
                If this is not specified, we raise `KeyError`.
            param_control (bool): if True, requests for parameter controls
                return the control object itself, as with any other control.
                If False, which is the default, they return the value
                stored in the control object; this is probably what
                you wanted.

        Returns:
            the value you asked for

        Raises:
            `KeyError`: if there is no element with the name you requested,
                and `default` was not specified.
            `ParseError`: if we attempted to complete the field name with
                `tokens`, but failed.
        """


        for k in kwargs.keys():
            if k not in ['default']:
                raise TypeError(f'{k} is an invalid keyword for get()')

        logger.debug("doc[%s], index=%s: getting value",
                repr(field), index)

        item, index = self._find_control_and_index(
                field = field,
                index = index,
                )

        if item is not None:
            if index is not None:
                index = int(index)
                result = item.get_element(index)
                logger.debug("doc[%s]:  -- %s[%s] == %s",
                        field, item, index, result)
            else:
                result = item

        elif 'default' in kwargs:
            result = kwargs['default']
            logger.debug("doc[%s]:  -- not found; returning default: %s",
                    field, result)

        else:
            logger.debug("doc[%s]:  -- not found",
                    field)
            raise KeyError(field)

        if (hasattr(result, 'is_queryable') and
                result.is_queryable and
                not param_control):

            t = result # save it for the log message
            result = result.query(tokens=None)

            logger.debug("%s:    -- the answer is the value of %s, == %s",
                    self, t, result)

        else:
            logger.debug("%s:    -- the answer is: %s (which is a %s)",
                    self, result, type(result))

        return result

    get = __getitem__

    def __delitem__(self, field,
            index = None,
            ):
        r"""
        Deletes an element, if you can.

        Args:
            field (`str`): the name of the element to delete.
                See the class description for a list of field names.
            index (int): if "field" refers to an array, this can be
                an index into it; if it isn't, this should be None
        """
        logger.debug("doc[%s], index=%s: getting value",
                repr(field), index)

        item, index = self._find_control_and_index(
                field = field,
                index = index,
                get_name_not_object = True,
                )

        if item is None:
            if index is None:
                raise KeyError(field)
            else:
                raise KeyError(f"{field};{index}")

        elif index is None:
            del self.controls[field]
        else:
            del self.controls[field][index]

    def _find_control_and_index(self, field, index,
            get_name_not_object = False,
            ):

        def get_control(name):

            if get_name_not_object:
                if name in self.controls:
                    return name
                else:
                    return None

            try:
                result = self.controls.get(name,
                        param_control = True,
                        )
                return result
            except KeyError:
                return None

        item = get_control(field)

        if item is not None:
            logger.debug("%s[%s]: found in controls table",
                    self, repr(field))
            return (item, None)

        m = re.match(KEYWORD_WITH_INDEX, field)

        if m is not None:
            if index is not None:
                raise ValueError(
                        'you supplied a number in the field name, '
                        'but index was not None'
                        )
            prefix, index = m.groups()

            item = get_control(prefix)

            logger.debug("%s[%s]: prefix==%s, index==%s, giving %s",
                    self, repr(field), prefix, index, item)

        return (item, index)

    @property
    def mode_list(self):
        """
        The working list of `self.mode`. Identical to `self.mode.list`.

        This exists so that `doc['mode_list']` works.
        You can also set this property.
        """
        return self.mode.list

    @mode_list.setter
    def mode_list(self,v): self.mode.list = v

    @property
    def created(self):
        """
        Timestamp of this doc's creation. Same as `created_at.timestamp()`.

        This exists so that `doc['created']` works.
        You can't set this property, unless you're Doctor Who,
        Marty McFly, or Bill and Ted.
        """
        return self.created_at.timestamp()

    def begin_group(self,
            flavour=None,
            **kwargs,
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

            Other arguments are passed to the constructor of Group
            (or of a subclass of Group).

        Raises:
            `ValueError`: if flavour is other than the options given above.

        Returns:
            `Group`. This is mainly useful to pass to `end_group()` to make
            sure the groups are balanced.
        """

        if flavour is None:
            new_group = Group(
                    doc = self,
                    **kwargs,
                    )
        elif flavour=='only-mode':
            try:
                delegate = self.groups[-1]
            except IndexError:
                delegate = None

            new_group = GroupOnlyForModes(
                    doc = self,
                    delegate = delegate,
                    **kwargs,
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
        # this used to do something ridiculous. Catch anyone calling it.
        # Take it out when we know there's nobody. July 2022.
        raise NotImplementedError()

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
            for item in box:
                self.paragraphs.add(item)
        else:
            self.paragraphs.add(box)

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

    def save(self):
        """
        Renders the document to the output driver specified
        by `doc['_output']`.

        Ends all open groups before it attempts to render.

        Raises:
            OSError: if something goes wrong during writing

        Returns:
            `None`
        """

        logger.debug("%s: saving document to %s", self,
                self.output)
        self.end_all_groups()
        self.mode.exercise_page_builder()
        self.paragraphs.close()

        tracingoutput = self.controls.get(
                r'\tracingoutput',
                param_control=True,
                )

        """9999
        if tracingoutput.value:
            for box in self.contents:
                for line in box.showbox():
                    tracingoutput.info(line)

        if not self.contents:
            logger.debug("%s:   -- but there was no output", self)
            print("note: there was no output")
            return
            """

        if not self.output:
            print("note: there was no output driver")
            return

        self.output.render()
        logger.debug("%s:   -- done!", self)

    @property
    @functools.cache
    def paragraphs(self):

        def _produce_page(page):
            logger.debug("%s: adding page to contents: %s",
                    self, page)
            self.contents.append(page)

        return yex.wrap.Paragraphs(doc=self,
                produce_page = _produce_page,
                )

    def __getstate__(self,
            full=True,
            raw=False,
            ):
        result = dict([k for k in self.items(
            full=full,
            raw=raw,
            )])
        return result

    def __setstate__(self, state):
        if state['_format']!=FORMAT_VERSION:
            raise ValueError("Format version was unknown")

        self.__init__()

        state = dict(state) # take a copy

        for cruft in [
                '_format', '_full', '_created', '_inputlineno',
                ]:
            if cruft in state:
                del state[cruft]

        for field, value in sorted(state.items()):
            logger.debug("doc.__setstate__: %s=%s", field, value)
            self[field] = value

        logger.debug("doc.__setstate__: done!")

    def __repr__(self):
        return '[doc]'

    def items(self, full=False, raw=False):
        if full:
            # we don't need anything to compare against
            blank = {}
        else:
            # get ourselves a fresh version of this class, so that
            # we know what's changed
            blank = dict(
                    [(k,v) for k,v in self.__class__().items(full=True)]
                    )

        return DocumentIterator(
                doc = self,
                full = full,
                raw = raw,
                blank = blank,
                )

class DocumentIterator:
    def __init__(self,
        doc,
        full,
        raw,
        blank,
        ):

        self.doc = doc
        self.full = full
        self.raw = raw
        self.blank = blank

    def __iter__(self):
        yield ('_format',  FORMAT_VERSION)
        yield ('_full',    self.full)
        yield ('_created', self.doc.created)

        def munge_value(v):

            if self.raw:
                return v
            elif hasattr(v, '__getstate__'):
                return v.__getstate__()
            else:
                return v

        def should_be_included(k, munged):

            if self.full:
                return True

            if k.startswith('_') and not k.startswith('__'):
                return False

            if k not in self.blank:
                return True

            if self.blank[k]==munged:
                return False

            return True

        for k in self.doc.controls.keys():

            # Look up v separately, rather than finding it via
            # controls.items(), to force instantiation.
            v = self.doc.controls.get(k, param_control=True)

            if hasattr(v, 'items'):

                for k2, v2 in v.items():
                    if hasattr(v2, '__getstate__'):
                        v2 = v2.__getstate__()

                    yield (k2, v2)

            else:

                # it doesn't provide its own items generator

                munged = munge_value(v)

                if should_be_included(k, munged):
                    yield (k, munged )

    def __repr__(self):
        return f'[{self.__class__.__name__};d={self.doc}]'

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
