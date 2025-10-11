r"`Document` holds a document while it's being processed."

import datetime
import yex
import yex.control.keyword
import yex.style
import re
import functools
from typing import Any, List, TextIO, Self, Union
from yex.document.callframe import Callframe
from yex.document.group import Group, ASSIGNMENT_LOG_RECORD
import yex.logging

logger = yex.logging.getLogger('document')

FORMAT_VERSION = 1
_NO_DEFAULT = ('no default,')

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

    def __init__(self,
            style = yex.style.Plain,
            ):

        self.created_at = datetime.datetime.now()

        self.style = style()

        self.controls = yex.control.ControlsTable(doc=self)
        self.controls |= yex.control.keyword.handlers()

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

    KEYWORD_WITH_INDEX = re.compile(r'^([^;]+?);?(-?[0-9]+)$')

    def open(self, what: (str|list|TextIO),
            **kwargs) -> 'yex.parse.Expander':

        r"""Opens a string, a list of characters, or a file for reading.

            Constructs a :obj:`Expander` on `what`.

            Args:
                what: where we're getting the symbols from.
                **kwargs: Arguments to pass to the `Expander`.
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

            Args:
                what: something to read characters from.
                **kwargs: Arguments to pass to the `Expander` which we'll
                    use to parse the input.
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
                    index: (int|None) = None,
                    param_control:bool = False,
                    from_restore:bool = False):
        r"""Assigns a value to an element of this doc.

            Args:
                field: the name of the element to change.
                    See the class description for a list of field names.
                value: the value to give the element.
                    Acceptable types and values depend on the field name.
                index: if "field" refers to an array, this can be
                    an index into it; if it isn't, this should be None
                from_restore: if True, we're in the process of
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

        if value is None:
            del self[field]
            return

        name = self._normalise_name(field)

        if from_restore:
            logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    'R', field, repr(value))
        elif self.globaldefs.value>0:
            logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    'G', field, repr(value))
        else:
            logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    '', field, repr(value))

            if self.groups:
                previous = self.get(name, default=None)
                self.groups[-1].remember_restore(field,
                        previous)

        logger.debug("doc[%s;%s] = %s",
                repr(field), index,
                value)

        item, index = self._find_control_and_index(
                field = field,
                index = index,
                )

        if item is not None and index is not None:

            index = int(index)

            logger.debug("=doc[%s]=%s: setting %s member %s",
                    repr(field), repr(value),
                    item, index,
                    )
            item.get_element(index=index).value=value

        elif param_control or item is None or not item.is_queryable:

            logger.debug("=doc[%s]=%s: setting control",
                    repr(field), repr(value))
            self.controls[field] = value

            #elif param_control or isinstance(value, yex.control.Control):
        else:
            logger.debug("=doc[%s]=%s: setting %s.value",
                    repr(field), repr(value),
                    item,
                    )
            item.value = value

    def __getitem__(self,
                    field:str,
                    index:Union[int,None]=None,
                    param_control:bool=False,
                    tokens:Union['Expander',None]=None,
                    **kwargs,
            ) -> Any:
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
            field: the name of the element to find.
                See the class description for a list of field names.
            index: if "field" refers to an array, this can be
                an index into it; if it isn't, this should be None
            tokens: used to find indexes for an array; see above
            default: what to return if there is no such element.
                If this is not specified, we raise `KeyError`.
            param_control: if True, requests for parameter controls
                return the control object itself, as with any other control.
                If False, which is the default, they return the value
                stored in the control object; this is probably what
                you wanted.

        Returns:
            the value you asked for, hopefully

        Raises:
            `KeyError`: if there is no element with the name you requested,
                and `default` was not specified.
            `ParseError`: if we attempted to complete the field name with
                `tokens`, but failed.
        """

        for k in kwargs.keys():
            if k not in ['default']:
                raise TypeError(f'{k} is an invalid keyword for get()')

        assert field is not None

        logger.debug("doc[%s;%s]: getting value",
                repr(field), index)

        item, index = self._find_control_and_index(
                field = field,
                index = index,
                )

        if item is not None:
            if index is not None:
                index = int(index)
                result = item.get_element(index)
            else:
                result = item

        elif default is not _NO_DEFAULT:
            result = default
            logger.debug("=doc[%s] not found; returning default: %s",
                    field, result)

        if len(field)==1:
            result = item
        else:
            logger.debug("=doc[%s]:  -- not found",
                    field)
            raise KeyError(field)

        if (hasattr(result, 'is_queryable') and
                result.is_queryable and
                not param_control):

            t = result # save it for the log message
            result = result.query(tokens=None)

            logger.debug("=the answer is the value of %s, == %s",
                    t, result)

        else:
            logger.debug("=the answer is: %s (which is a %s)",
                    result, type(result))

        return result

    get = __getitem__

    def __delitem__(self,
                    field:str,
                    index:(int|None) = None,
            ):
        r"""
        Deletes an element, if you can.

        Args:
            field: the name of the element to delete.
                See the class description for a list of field names.
            index: if "field" refers to an array, this can be
                an index into it; if it isn't, this should be None
        """
        logger.debug("doc[%s;%s]: getting value, to delete it",
                repr(field), index)

        name = self._normalise_name(field)

        if len(name)==1:
            del self.controls[name[0]]
        else:
            del self.controls[name[0]][name[1]]

    def _find_control_and_index(self,
                                field:str,
                                index:Union[int, None],
                                get_name_not_object:bool = False,
                                ):

        def get_control(name:str) -> Union[yex.control.Control, None]:

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
            logger.debug("doc[%s]: found in controls table",
                    repr(field))
            return (item, None)

        m = re.match(self.KEYWORD_WITH_INDEX, field)

        if m is not None:
            if index is not None:
                raise ValueError(
                        'you supplied a number in the field name, '
                        'but index was not None'
                        )
            prefix, index = m.groups()

            item = get_control(prefix)

            logger.debug("doc[%s]: prefix==%s, index==%s, giving %s",
                    repr(field), prefix, index, item)

        return (item, index)

    @classmethod
    def _normalise_name(cls, name):
        r"""
        Normalises a name which can be passed to __getitem__ or __setitem__.

        Args:
            name (`str`, or `(str, int)`, or `(str,)`): a name.

                If it's a tuple of `(str)`, or `(str, int)`, it's
                returned unchanged.

                The equivalent lists are converted to tuples and returned.

                If it's a simple string and it matches KEYWORD_WITH_INDEX,
                the keyword and index are extracted and returned as a tuple.
                For example:
                    - `"fred23"` returns `("fred", 23)`
                    - `"fred23;45"` returns `("fred", 45)`

                For any other simple string, we return a tuple of that string.

                For any other value, we throw TypeError.
        """

        if isinstance(name, str):
            m = re.match(cls.KEYWORD_WITH_INDEX, name)

            if m is None:
                return (name,)

            g = m.groups()
            return (g[0], int(g[1]))

        elif not isinstance(name, (tuple, list)):
            raise TypeError(
                    "name must be str, tuple, or list, and not {type(name)}")

        elif not isinstance(name[0], str):
            raise TypeError(
                    "name[0] must be str, and not {type(name[0])}")

        elif len(name)==1:
            return (name[0],)

        elif len(name)!=2:
            raise TypeError(
                    "name must have 1 or 2 members, or be str")

        elif not isinstance(name[1], int):
            raise TypeError("name[1] must be int, and not {type(name[1])}")

        else:
            return (name[0], name[1])

    def begin_group(self,
            **kwargs,
            ):
        r"""
        Opens a new group.

        Called by ``{`` and ``\begingroup``.

        Keyword arguments are passed to the constructor of Group.

        Returns:
            `Group`. This is mainly useful to pass to `end_group()` to make
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

        Called by ``}`` and ``\endgroup``.

        Args:
            group: the group we should be closing.
                This only functions as a check; we can only close the
                top group in the stack. If this is None, which is the
                default, we just close the top group without doing a check.

            from_endgroup: if True, we got here from an
                ``\end_group`` command; if False, we got here from a ``}``
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

    def remember_restore(self, f:Any, v:Any):
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

    def shipout(self, box: Union['Box', List['Box']]):
        """
        Sends a box, or multiple boxes, to the output queue.

        Anything passed to this method will be stored, rather than
        rendered immediately. It will be rendered when the `save` method
        is called.

        Args:
            box: a box or boxes to be rendered.

        Returns:
            `None`
        """

        if isinstance(box, list):
            for item in box:
                self.paragraphs.add(item)
        else:
            self.paragraphs.add(box)

    def end_all_groups(self,
                       tokens: Union['Expander', None] = None,
            ):
        """
        Closes all open groups.

        Args:
            tokens: the token stream we're reading.
                This is only needed if one of the groups we're ending
                has produced a list which now has to be handled.

        Returns:
            `None`.
        """
        logger.debug("ending all groups: %s", self.groups)
        while self.groups:
            self.end_group(
                    tokens=tokens,
                    )
        logger.debug("=done ending all groups")

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

    def __setstate__(self, state:dict):
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

    def __repr__(self):
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
        yield ('_format',  FORMAT_VERSION)
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
