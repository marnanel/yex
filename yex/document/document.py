r"`Document` holds a document while it's being processed."

import datetime
import yex
import yex.keyword
import yex.style
import re
import functools
from typing import Any, List, TextIO, Self, Union, Mapping
from yex.document.callframe import Callframe
from yex.document.group import Group, ASSIGNMENT_LOG_RECORD
import yex.logging

logger = yex.logging.getLogger('document')

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
        For example, `doc['\if']`. Don't include the backslash prefix.
    - The name of any user-defined macro.
    - The name of any register.
        For example, `doc['\count23']` or `doc['\box12']`.
    - The prefix of any register, such as `doc['\count']`
        You must supply `tokens`, so we can find the rest of it.
    - Some internal special values:
        - `doc['_font']`, for the current font.
        - `doc['_mode']`, for the current mode.
    - A few controls can themselves be subscripted.
        Writing `doc['\font3']` is equivalent to writing
        `doc['\font'][3]`.

        The second subscript must be an integer,
        and can be negative. You can also separate the field name
        from the field subscript with a semicolon. So
        `doc['font;3']`, `doc['font3']`, and `doc['font'][3]`
        are equivalant. `doc['cmr10;3']` couldn't be written
        without the semicolon.

    Attributes:
        created_at (datetime.Datetime): when the Document was
            constructed. This provides initial values for
            TeX's time-based parameters, such as `\year`.
        controls (yex.controls.ControlsTable): all the controls defined,
            both built-in and user-defined.
        groups (List[yex.document.Group]): the nested groups
            of the TeX source being processed, which are
            created either by `{` and `}` or by
            `\begingroup` and `\endgroup`.
        fonts (Mapping[str, Font]): fonts currently loaded.
            They need not have identifiers in the controls
            table, but they're not accessible from TeX code
            unless they do.
        font (yex.font.Font): the currently selected font.
        mode (yex.mode.Mode): the currently selected mode.
        output (yex.output.Output): the output driver. For example,
            the PDF driver or the SVG driver.
        contents (List[yex.box.Box]): the rendered contents
            waiting to go to the output driver.
        parshape (List[yex.value.Dimen]): you probably don't
            need to look at this. It's a list of constraints on lengths
            of lines in the current paragraph, set by `\parshape`
            but kept here so it persists.
        ifdepth (_Ifdepth_List): essentially a list of booleans,
            representing whether particular conditional clauses are
            executing. For example, after `\iftrue` the top member
            will be True, after `\iffalse` it will be False, and
            `\else` will (generally) negate the top member.
        style (yex.style.Style): a stylesheet-- that is, a module
            which runs a particular file before we read the main document.
            The usual example is yex.style.Plain, which
            represents `plain.tex`.
    """

    FORMAT_VERSION = 1
    KEYWORD_WITH_INDEX = re.compile(r'^([^;]+?);?(-?[0-9]+)$')

    def __init__(self,
                 style:yex.style.Style = yex.style.Plain,
                 ):

        self.created_at = datetime.datetime.now()

        self.style = style()

        self.controls = yex.control.ControlsTable(doc=self)
        self.controls |= yex.keyword.handlers()

        self.fonts = {}

        self.groups = []

        self.parshape = None

        self.ifdepth = _Ifdepth_List([True])
        self.call_stack = []

        self.font = yex.font.Font.from_name(
                name=None,
                doc=self,
                )
        self.mode = self.outermost_mode = yex.mode.Vertical(
                doc=self,
                is_outermost=True,
                )

        self.output = None
        self.contents = []

        self.controls |= {
                '_inputs': yex.io.StreamsTable(doc=self,
                our_type=yex.io.InputStream),
                '_outputs': yex.io.StreamsTable(doc=self,
                our_type=yex.io.OutputStream),
                }

        # for easy access:
        for name in [
                'tracingcommands',
                'globaldefs',
                'inputlineno',
                ]:
            setattr(self, name,
                    self.controls.get('\\'+name,
                                      param_control=True,
                                      ),
                    )

        logger.debug("created, with style %s", self.style)

    def open(self, what: (str|list|TextIO),
            **kwargs) -> 'yex.parse.Expander':

        r"""Opens a string, a list of characters, or a file for reading.

            Constructs an `Expander` on `what`.
            All kwargs are passed to the `Expander`.

            Args:
                what: where we're getting the symbols from.
            """
        e = yex.parse.Expander(
                what,
                doc = self,
                **kwargs,
                )
        return e

    def read(self,
             what: (str|TextIO),
            **kwargs) -> None:
        r"""Reads a string, or a file, and adds it to this Document.

            All kwargs are passed to the `Expander`, which we'll
            use to parse the input.

            Args:
                what: something to read characters from.
        """

        logger.debug("reading from %s, with params %s", what, kwargs)

        e = self.open(what, **kwargs)

        logger.debug(">reading through %s", e)

        for item in e:
            logger.debug("resulting in: %s", item)

            if item is None:
                break

            self.mode.handle(
                    item=item,
                    tokens=e,
                    )

        logger.debug("<done reading", self)

    def __iadd__(self, thing: (str|TextIO)) -> Self:
        r"""Short for `read(thing)`. See `read` for more information.

            Args:
                thing: something to read characters from.
        """
        self.read(thing)

        return self

    def __setitem__(self,
                    field: str,
                    value: Any,
                    ):
        """
        See under set().
        """
        self._inner_set(
                field = field,
                value = value,
                )

    def set(self,
            field: str,
            value: Any,
            ):
        r"""
        Assigns a value to an element of this doc.

        Args:
            field: the name of the element to change.
                See the class description for a list of field names.
            value: the value to give the element.
                Acceptable types and values depend on the field name.
                Passing None is exactly equivalent to calling
                `doc.delete(field)`.

        Raises:
            KeyError: if the field doesn't name an element
            TypeError: if the value has the wrong type for the field
            ValueError: if there's something wrong with the value
        """
        self._inner_set(
                field = field,
                value = value,
                )

    def set_control(self,
            field: str,
            value: 'yex.control.Control',
            ):
        r"""
        Sets a control in our control table.

        This is like `doc.controls.get()`, except that it understands
        indexes: `set_control('\count23', ...)` will set the register
        for `\count23`.

        Args:
            field: the name of a control, possibly including an index

        Raises:
            KeyError: if there is no such control
        """
        self._inner_set(
                field = field,
                value = value,
                param_control = True,
                )

    def _inner_set(self,
                   field: str,
                   value: Any,
                   index: (int|None) = None,
                   param_control:bool = False,
                   from_restore:bool = False):
        r"""
        Assigns a value to an element of this doc.

        Args:
            field: the name of the element to change.
                See the class description for a list of field names.
            value: the value to give the element.
                Acceptable types and values depend on the field name.
                Passing None is exactly equivalent to calling
                `doc.delete(field)`.
            index: if "field" refers to an array, this can be
                an index into it; if it isn't, this should be None
            from_restore: if True, we're in the process of
                restoring settings at the end of a group; otherwise,
                we're not, and we store a record of this assignment
                until we are. You probably don't need to use this.
            param_control: if True, requests to set parameter controls
                set the control object itself, as with any other control.
                If False, which is the default, they set the value
                stored in the control object; this is probably what
                you wanted.

        Raises:
            KeyError: if the field doesn't name an element
            TypeError: if the value has the wrong type for the field
            ValueError: if there's something wrong with the value
        """

        if value is None:
            self.delete(field=field)
            return

        name, index = self._parse_name(field, index)

        if from_restore:
            logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    'R', name, repr(value))
        elif self.globaldefs.value>0:
            logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    'G', name, repr(value))
        else:
            logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    '', name, repr(value))

            if self.groups:
                try:
                    previous = self._inner_get(
                            field=name,
                            index=index,
                            )
                except KeyError:
                    previous = None
                self.groups[-1].remember_restore(field,
                        previous)

        logger.debug("doc[%s;%s] = %s",
                repr(name), index,
                value)

        try:
            item = self.controls.get(name,
                                     param_control = param_control,
                                     )
        except KeyError:
            item = None

        if item is not None and index is not None:

            logger.debug("=doc[%s]=%s: setting %s member %s",
                    repr(name), repr(value),
                    item, index,
                    )
            item.get_element(index=index).value=value

        elif param_control or item is None or not hasattr(item, 'query'):

            logger.debug("=doc[%s]=%s: setting control",
                    repr(name), repr(value))
            self.controls[name] = value

        else:
            logger.debug("=doc[%s]=%s: setting %s.value",
                    repr(name), repr(value),
                    item,
                    )
            item.value = value

    def get(self,
            field:str,
            tokens: Union['Expander',None]=None,
            default: Any=None,
            ) -> Any:
        r"""
        Retrieves the value of an element of this doc.

        Args:
            field: the name of the element to find.
                See the class description for details of field names.
            default: what to return if there is no such element.
                If you'd rather get an exception, use `__getitem__`
                instead.
            tokens: used to find an integer index for an array.
                For example, the count register numbered 23 is named
                `"\count23"`, but this name is three tokens if you write
                it in TeX: `\count`, `2`, and `3`.

                Thus if you write
                ```
                get(field=r'\count', tokens=expander)
                ```

                we read the next characters of the expander.
                If they were `2` and `3`, you would get the value
                of `\count23`.

                This behaviour is handled by the keyword class,
                so it's possible that `tokens=None` does something
                useful. Check the docstring for that class to be sure.

        Returns:
            the value you asked for, hopefully.
                Otherwise, the default you specified

        Raises:
            ParseError: if we attempted to complete the field name with
                `tokens`, but failed.
        """

        try:
            return self._inner_get(
                    field = field,
                    tokens = tokens,
                    )
        except KeyError:
            return default

    def __getitem__(self,
                    field:str,
                    ) -> Any:
        r"""
        Retrieves the value of an element of this doc.

        The remarks in the docstring for Document.get() about `tokens=None`
        apply to this method too.

        Args:
            field: the name of the element to find.
                See the class description for details of field names.

        Returns:
            the value you asked for, hopefully

        Raises:
            KeyError: if there is no element with the name you requested,
                and `default` was not specified.
            ParseError: if you asked for an array, and we couldn't figure out
                how to complete the request without a token stream.
        """
        return self._inner_get(
                field = field,
                )

    def get_control(self,
                    field:str,
                    ) -> Any:
        r"""
        Retrieves a control from our control table.

        This is like `doc.controls.get()`, except that it understands
        indexes: `get_control('\count23')` will get you the register
        for `\count23`.

        Args:
            field: the name of a control, possibly including an index

        Returns:
            a control

        Raises:
            KeyError: if there is no such control
        """
        return self._inner_get(
                field = field,
                param_control = True,
                )

    def _inner_get(self,
                   field:str,
                   index:Union[int,None]=None,
                   param_control:bool=False,
                   tokens:Union['Expander',None]=None,
                   ) -> Any:
        name, index = self._parse_name(field, index)

        logger.debug("doc[%s;%s]: getting value",
                repr(name), index)

        result = self.controls.get(name,
                                   param_control = param_control,
                                   )

        if index is not None:
            result = result.get_element(index)

        if hasattr(result, 'query') and not param_control:

            t = result # save it for the log message
            result = result.query(tokens=None)

            logger.debug("=the answer is the value of %s, == %s",
                    t, result)

        else:
            logger.debug("=the answer is: %s (which is a %s)",
                    result, type(result))

        return result

    def __delitem__(self,
                    field:str,
            ):
        r"""
        See delete().
        """
        self.delete(
                field = field,
                )

    def delete(self,
               field:str,
                  ):
        r"""
        Deletes an element, if you can.

        In most cases, this removes the named element from the
        document's controls table. For registers, such as `\count23`,
        the deletion is handled by their array, so the meaning may
        differ. For example, deleting `\count23` simply sets its
        value to zero.

        Args:
            field: the name of the element to delete.
                See the class description for details of field names.
        """
        logger.debug("doc[%s]: getting value, to delete it",
                repr(field))

        name, index = self._parse_name(field, None)

        if index is None:
            del self.controls[name]
        else:
            del self.controls[name][index]

    @classmethod
    def _parse_name(cls,
                    field:str,
                    index:Union[int, None],
                    ) -> (str, Union[int, None]):
        """
        Parses a name which can be passed to __getitem__ or __setitem__
        or __delitem__, or their associated methods.

        Args:
            field: a string naming a field in our controls table.
                If it ends with an optional semicolon followed by
                a decimal integer, then this suffix is removed,
                and treated as if it had been supplied as an index.
                In such a case, the "index" argument must be None.

                For example:
                    - `"fred23"` is equivalent to `("fred", 23)`
                    - `"fred23;45"` is equivalent to `("fred23", 45)`

            index: a possible index into the named field.

        Returns:
            (str, int)

        Raises:
            ValueError: if "field" supplies an index but "index" is not None.
        """

        field = str(field)
        if index is not None:
            index = int(index)

        m = re.match(cls.KEYWORD_WITH_INDEX, field)

        if m is None:
            return (field, index)

        if index is not None:
            raise ValueError(
                    f"{field} specifies an index, but {index} is not None")

        g = m.groups()
        return (g[0], int(g[1]))

    def begin_group(self,
            **kwargs,
            ):
        r"""
        Opens a new group.

        Called by `{` and `\begingroup`.

        Keyword arguments are passed to the constructor of Group.

        Returns a Group; you can usually discard this, but it's
        also useful to pass to `end_group()` to make
        sure the groups are balanced.
        """

        new_group = Group(
                doc = self,
                **kwargs,
                )

        self.groups.append(new_group)
        logger.debug("%sStarted group: %s",
                '  '*len(self.groups),
                self.groups)

        return new_group

    def end_group(self,
                  group:(Group|None)=None,
                  from_endgroup:(bool|None)=None,
                  tokens: Union['yex.parse.Expander', None]=None,
            ):
        r"""
        Closes a group.

        Discards all settings made since the most recent `begin_group()`,
        except global settings.

        Called by `}` and `\endgroup`.

        Args:
            group: the group we should be closing.
                This only functions as a check; we can only close the
                top group in the stack. If this is None, which is the
                default, we just close the top group without doing a check.

            from_endgroup: if True, we got here from an
                `\end_group` command; if False, we got here from a `}`
                token; if None, we got here some other way. If this is
                non-None, it gets matched against the `from_begingroup`
                property of the group we're closing.

            tokens: the token stream we're reading.
                This is only needed if the group we're ending has produced
                a list which now has to be handled.

                This argument *can* be `None`, if you're sure that won't
                happen; if it does, and the handler needs a token stream,
                you'll get an error from the handler.

        Raises:
            `YexError`: if there are no groups remaining.
        """

        if not self.groups:
            raise yex.exception.MoreGroupEndedThanBeganError()

        logger.debug("closing %s; from_endgroup==%s",
                self.groups[-1], from_endgroup)

        if (from_endgroup is not None and
                from_endgroup!=self.groups[-1].from_begingroup):

            if self.groups[-1].from_begingroup:
                needed = r'\begingroup'
            else:
                needed = '{'

            if from_endgroup:
                found = r'\endgroup'
            else:
                found = '}'

            raise yex.exception.WrongKindOfGroupError(
                    needed = needed,
                    found = found,
                    )

        if group is not None and self.groups[-1]!=group:
            raise ValueError(
                    f"expected to close group {group}, "
                    f"but group {self.groups[-1]} is the next one to close.")

        self.groups.pop().run_restores()

    def showlists(self) -> None:
        r"""
        Prints details of the list in the current `Mode`, and of all
        the containers it contains, and all the containers *they* contain,
        and so on.

        Implements the `\showlists` debugging command:
        see p88 of the TeXbook.

        Currently disabled.
        """
        raise NotYetImplemented()

    def __len__(self) -> int:
        # this used to do something ridiculous. Catch anyone calling it.
        # Take it out when we know there's nobody. July 2022.
        raise NotImplementedError()

    def remember_restore(self, f:str, v:Any) -> None:
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
        self.groups[-1].remember_restore(f,v)

    def shipout(self, box: Union['Box', List['Box']]) -> None:
        """
        Sends a box, or multiple boxes, to the output queue.

        Anything passed to this method will be stored, rather than
        rendered immediately. It will be rendered when the `save` method
        is called.

        Args:
            box: a box or boxes to be rendered.
        """

        if isinstance(box, list):
            for item in box:
                self.paragraphs.add(item)
        else:
            self.paragraphs.add(box)

    def end_all_groups(self,
                       tokens: Union['Expander', None] = None,
            ) -> None:
        """
        Closes all open groups.

        Args:
            tokens: the token stream we're reading.
                This is only needed if one of the groups we're ending
                has produced a list which now has to be handled.
        """
        logger.debug("ending all groups: %s", self.groups)
        while self.groups:
            self.end_group(
                    tokens=tokens,
                    )
        logger.debug("=done ending all groups")

    def save(self) -> None:
        """
        Renders the document to the output driver specified
        by `doc['_output']`.

        Ends all open groups before it attempts to render.

        Raises:
            OSError: if something goes wrong during writing
        """

        logger.debug("saving document to %s", self.output)
        self.end_all_groups()

        while not self.mode == self.outermost_mode:
            self.mode.close()

        self.outermost_mode.exercise_page_builder()
        self.paragraphs.flush()

        tracingoutput = self.controls.get(
                r'\tracingoutput',
                param_control=True,
                )

        if not self.output:
            print("note: there was no output driver")
            return

        self.output.render()

    @property
    @functools.cache
    def paragraphs(self) -> yex.wrap.Paragraphs:

        def _produce_page(page):
            logger.debug("adding page to contents: %s",
                    page)
            self.contents.append(page)

        return yex.wrap.Paragraphs(doc=self,
                produce_page = _produce_page,
                )

    def __getstate__(self,
                     full:bool=True,
                     raw:bool=False,
                     ) -> dict:
        result = dict([k for k in self.items(
            full=full,
            raw=raw,
            )])
        return result

    def __setstate__(self, state:dict) -> None:
        if state['_format']!=self.FORMAT_VERSION:
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

    def __repr__(self) -> str:
        return '[doc]'

    def items(self, full:bool=False, raw:bool=False) -> List:
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
                 doc:Document,
                 full:bool,
                 raw:bool,
                 blank:dict,
        ):

        self.doc = doc
        self.full = full
        self.raw = raw
        self.blank = blank

    def __iter__(self):
        yield ('_format',  Document.FORMAT_VERSION)
        yield ('_full',    self.full)
        yield ('_created', self.doc.created_at)

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
        def _repr(v:Any) -> str:
            if v==True:
                return 'T'
            elif v==False:
                return 'f'
            else:
                return repr(v)
        result = ''.join([_repr(v) for v in self])
        return result
