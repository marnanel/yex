import logging
import enum
import string
import yex.exception
import yex.util
from yex.parse.source import *
from yex.parse.token import *
from yex.parse.tokeniser import *

logger = logging.getLogger('yex.general')

class _ExpanderIterator:

    SPIN_LIMIT = 1000

    def __init__(self, expander):
        self.expander = expander
        self.spun_on_none = 0

    def __iter__(self):
        return self

    def __next__(self):
        result = self.expander.next()

        if result is None:
            self.spun_on_none += 1

            if self.spun_on_none > self.SPIN_LIMIT:
                raise yex.exception.SpinOnNoneError(
                        spins = self.spun_on_none,
                        caller = yex.util.show_caller,
                        )
        else:
            self.spun_on_none = 0

        return result

class RunLevel(enum.IntEnum):
    r"""
    Levels you can run an Expander at.

    Attributes:
        DEEP: direct access to the source beneath.
            For example, this will emit group delimiters
            rather than using them to start or end groups.
            This can only be used with next(), rather than
            with iterators, and you probably don't want to use it.

        READING: the expander will handle most kinds of
            token for you. But it will emit all control tokens,
            whether expandable or unexpandable, as well as
            all active tokens, and all LETTERs and OTHERs.
            This is the lowest level in common use.

        EXPANDING: like READING, except that the expander will
            only return control tokens for unexpandable controls.
            It will run any expandable controls for you.
            For example, you won't see any of the symbols
            between \iffalse and \fi, and you won't see any
            user-defined macros.

        EXECUTING: like EXPANDING, except that unexpandable controls
            and active tokens will be run rather than emitted.
            If the result is another such item, that will be run too,
            and so on. When the expander ends up with something else, it
            will emit that.

        QUERYING: like EXECUTING, except that items with a value
            will be returned rather than executed.
            The item itself is returned, not its value.
    """
    DEEP = 10
    READING = 20
    EXPANDING = 30
    EXECUTING = 40
    QUERYING = 41

def _runlevel_by_name(name):
    if isinstance(name, (RunLevel, int)):
        return RunLevel(name)
    elif name=='deep':
        return RunLevel.DEEP
    elif name=='reading':
        return RunLevel.READING
    elif name=='expanding':
        return RunLevel.EXPANDING
    elif name=='executing':
        return RunLevel.EXECUTING
    elif name=='querying':
        return RunLevel.QUERYING
    elif name is None:
        return None
    else:
        raise yex.exception.WeirdRunLevelError(
                level = name,
                )

ON_EOF_OPTIONS = set(('none', 'raise', 'exhaust'))

BOUNDED_OPTIONS = set(('no', 'balanced', 'single'))

class Expander:

    r"""Interprets a TeX file, and expands its macros.

    Takes a source, and iterates over it,
    returning the tokens with the macros expanded
    according to the definitions
    stored in the Document attached to that source.

    By default, Expander will keep returning None forever,
    which is what you want if you're planning to do
    lookahead. If you're going to put this Expander into
    a `for` loop, you'll want to set `on_eof="exhaust"`.

    It's fine to attach another Expander to the
    same source, and to run it even when this
    one is active.

    Attributes:
        source: the source
        doc (`yex.Document`): the document we're helping create.
        bounded (str): one of:
            - `single`: iteration stops after a single
                character, or after a balanced group if the
                next character is a BEGINNING_GROUP.
            - `balanced`: the same except that a BEGINNING_GROUP is required.
            - `no`, which is the default: iteration ends when the
                source ends.

            If you want just one character, look into using `next()`.

            Any value here but `no` requires `on_eof='exhaust'`.

        level (`RunLevel` or `str`): the level to run at;
            see the documentation for RunLevel for further information.
            Default is 'executing'.
        on_eof (`str`): what to do if we reach the end of the file.
            Use `"none"` to return `None` forever, `"raise"` to
            raise `UnexpectedEOFError`, or `"exhaust"`
            to exhaust the iterator.
        no_outer (bool): if True, attempting to call a macro which
            was defined as "outer" will cause an error.
            Defaults to False.
        on_push (ExpandAfter or None): if non-None, this will
            be called every time an item is pushed, as documented
            on the push() method.
        delegate (Expander or None): if non-None, then when next()
            is called, it will return the next value from this
            Expander. When the Expander is exhausted, the field will
            be reset to None. This should have on_eof='exhaust'
            unless you're into heavy wizardry and pain.
    """

    def __init__(self, source,
            bounded = 'no',
            level = RunLevel.EXECUTING,
            on_eof = 'none',
            no_outer = False,
            on_push = None,
            doc = None,
            pushback = None,
            ):

        if on_eof not in ON_EOF_OPTIONS:
            raise ValueError('on_eof must be one of: '
                    f'{" ".join(sorted(ON_EOF_OPTIONS))}')

        if bounded not in BOUNDED_OPTIONS:
            raise ValueError('bounded must be one of: '
                    f'{" ".join(sorted(BOUNDED_OPTIONS))}')

        if bounded!='no':
            if on_eof!='exhaust':
                raise ValueError(
                        'unless bounded is "no", on_eof must be "exhaust"')

        self.bounded = bounded
        self.level = _runlevel_by_name(level)
        self.on_eof = on_eof
        self.no_outer = no_outer
        self.on_push = on_push
        self._bounded_limit = None
        self.delegate = None
        self.doc = doc
        self.pushback = pushback

        if isinstance(source, Tokeniser):
            self.source = source

            if doc is None:
                self.doc = self.source.doc

        elif doc is None:
            raise ValueError('If "source" is not a Tokeniser, you must '
                    'supply "doc".')
        else:
            # If pushback is None, the Tokeniser will create a Pushback
            # for us.

            self.source = Tokeniser(
                    doc = doc,
                    source = source,
                    pushback = pushback,
                    )

        if self.pushback is None:
            self.pushback = self.source.pushback

        # For convenience, we allow direct access to some of
        # Tokeniser's methods.
        for name in [
                'eat_optional_char',
                'optional_string',
                'error_position',
                'exhaust_at_eol',
                ]:
            setattr(self, name, getattr(self.source, name))

        logger.debug("%s: ready; called from %s",
                self,
                yex.util.show_caller,
                )

    def __iter__(self):
        return _ExpanderIterator(self)

    def another(self, **kwargs):
        """
        Returns an expander like this one, with given changes to its behaviour.

        The result will be an Expander on the same Tokeniser.
        If there are no changes requested, or if the changes requested
        make no difference, the result will be this same Expander;
        otherwise it will be a new Expander.

        Any setting specified in `kwargs` will be honoured.
        `bounded` will revert to `'no'` unless it's specified in `kwargs`.
        All other settings will be copied from this Expander.

        Returns:
            `Expander`
        """
        our_params = {
                'source': self.source,
                'bounded': 'no',
                'level': self.level,
                'on_eof': self.on_eof,
                'no_outer': self.no_outer,
                'on_push': self.on_push,
                'doc': self.doc,
                }
        new_params = our_params | kwargs

        if 'source' in kwargs and 'pushback' not in kwargs:
            new_params['pushback'] = self.pushback.another()

        if our_params==new_params:
            logger.debug(
                    ( "%s: not spawning another Expander; no changes "
                    "requested (called from %s)"),
                    self,
                    yex.util.show_caller,
                    )
            return self
        else:
            logger.debug(
                    ("%s: spawning another Expander with changes: %s; "
                    "called from %s"),
                    self,
                    kwargs,
                    yex.util.show_caller,
                    )
            result = Expander(**new_params)
            return result

    def next(self,
            **kwargs,
            ):
        r"""
        Returns the next item.

        This is just like next() on an iterator, but with more options.
        (And indeed, our iterators are implemented in terms of this method.)

        Args:
            as for another().

        Raises:
            `UnexpectedEOFError` on unexpected end of file, or if
            `no_outer` finds the appropriate problem.

        Returns:
            `Token`
        """

        source = self._source_for_next.another(**kwargs)

        if source.level==RunLevel.DEEP:
            result = source._next_at_deep()
        elif source.level in [RunLevel.READING, RunLevel.EXPANDING]:
            result = source._next_at_reading_or_expanding()
        elif source.level in [RunLevel.EXECUTING, RunLevel.QUERYING]:
            result = source._next_at_executing_or_querying()
        else:
            assert False, f'unknown runlevel: {source.level}'

        logger.debug("%s:     -- found %s",
                self, result)

        if self.bounded!='no' and self._bounded_limit is None:
            # This must be the first next() since we started.
            # Let's see whether we've been given a single item.

            if isinstance(result, BeginningGroup):
                # we need to read a balanced pair.
                self._bounded_limit = self.pushback.group_depth

                logger.debug(
                        "%s:        -- opens bounded expansion, read again",
                        self)
                result = self.next()
            elif self.bounded=='balanced':
                # First result wasn't a BeginningGroup,
                # but it should have been.
                raise yex.exception.NeededBalancedGroupError(
                        problem=result)
            else:
                # First result wasn't a BeginningGroup,
                # so we handle it and then stop.
                logger.debug("%s:  -- the only symbol in a bounded expansion",
                        self)
                self.source = None

        if self._bounded_limit is not None:
            if self.pushback.group_depth < self._bounded_limit:
                logger.debug(
                        ('%s: end of bounded expansion: group depth is %s, '
                        'which is below the starting limit, %s'
                            ),
                        self, self.pushback.group_depth,
                        self._bounded_limit,
                        )
                self.source = None
                result = None

        if result is None:

            if self.delegate is not None:
                logger.debug(
                        ('%s: delegate %s is all done; '
                        'carrying on with our own stuff'),
                        self, self.delegate,
                        )
                self.delegate = None
                return self.next(**kwargs)

            if source.on_eof=="raise":
                logger.debug("%s: unexpected EOF", self)
                raise yex.exception.UnexpectedEOFError()
            elif source.on_eof=="exhaust":
                raise StopIteration

        return result

    def _next_via_delegate(self, **kwargs):

        assert self.delegate is not None

        logger.debug("%s: delegating to %s, with kwargs %s",
                self, self.delegate, kwargs)

        result = self.delegate.next(**kwargs)

        if result is None:
            logger.debug("%s: delegate %s is exhausted",
                    self, self.delegate)
            self.delegate = None
            return self.next(**kwargs)

        return result

    def _next_at_deep(self):

        assert self.level==RunLevel.DEEP

        if self.source is None:
            return None

        while True:
            result = next(self.source)
            if isinstance(result, yex.parse.Internal):
                result(self)
            else:
                break

        if self.no_outer and isinstance(result, yex.parse.Control):

            # We have to enforce no_outer.

            referent = self.doc.get(
                    result.identifier,
                    default = None,
                    param_control = True,
                    )

            if getattr(referent, 'is_outer', False):
                logger.debug("%s: -- which -> %s, which is outer",
                        self, referent)
                raise yex.exception.OuterOutOfPlaceError(
                        problem = result.identifier,
                        )

        return result

    @property
    def _source_for_next(self):
        r"""
        Where we're getting the next item from.

        That's self.delegate if it's set. Otherwise, it's ourselves.

        A delegate may have a delegate of its own, but that makes no
        difference to us.

        This only applies to level=="querying" or "executing",
        and to our next() method itself. Other levels get their items
        directly from the source.

        Returns:
            Expander
        """
        if self.delegate is not None:
            logger.debug("%s: delegating to %s",
                    self, self.delegate)

            return self.delegate
        else:
            return self

    def _next_at_reading_or_expanding(self):
        r"""
        Finds the next item in the input at level=="reading" or
        level=="expanding".

        This method is not written as a generator because it
        needs to be recursive.
        """

        assert self.level!=RunLevel.DEEP

        while True:
            if self._bounded_limit is not None and self.source is not None:
                if self.pushback.group_depth < self._bounded_limit:
                    self.source = None
                    logger.debug("%s: end of bounded expansion", self)

            if self.source is None:
                logger.debug("%s: all done; returning None", self)
                return None

            token = next(self.source)

            logger.debug("%s: token: %s",
                    self,
                    token,
                    )

            if not hasattr(token, 'category'):
                # Not a token. Could be a Control, could be some
                # other class, could be None. Anyway, it's not our problem;
                # pass it through.
                if self.doc.ifdepth[-1]:

                    if hasattr(token, 'is_array') and token.is_array:
                        logger.debug(
                            "%s  -- not a token: %s; looking up index",
                                self, token,)

                        token = token.get_element_from_tokens(self)
                        logger.debug("%s  -- found: %s; passing through",
                                self, token,)
                        self.source.eat_whitespace_after_control()

                    else:
                        logger.debug("%s  -- not a token; "
                                "passing through: %s",
                                self, token,)

                    return token
                else:
                    logger.debug("%s  -- not passing %s because "
                            "of a conditional",
                            self, token)
                    continue

            if isinstance(token, (Control, yex.parse.Active)):

                name = token.identifier

                handler = self.doc.get(name,
                        default=None,
                        param_control=True)

                if handler is None:
                    if self.doc.ifdepth[-1]:
                        logger.debug(
                                "%s: %s is undefined; returning it",
                                self, token)
                        return token
                    else:
                        logger.debug(
                                "%s: %s is undefined; not returning it "
                                "because of a conditional",
                                self, token)
                        continue

                elif self.level>=RunLevel.EXPANDING and \
                        handler.is_array and \
                        self.doc.ifdepth[-1]:

                    logger.debug((
                        "%s: found control %s (which is a %s) "
                        "and it's an array; looking up an element"),
                        self, handler, type(handler))

                    index = yex.value.Value.get_value_from_tokens(self)

                    logger.debug("%s:   -- element %s",
                        self, index)

                    handler = handler.get_element(index=index)

                    logger.debug("%s:   -- element %s found: %s",
                        self, index, handler)
                    self.source.eat_whitespace_after_control()

                if not isinstance(handler, yex.control.Expandable):
                    if self.doc.ifdepth[-1]:
                        logger.debug(
                                '%s: %s is unexpandable; returning it',
                                self, handler)
                        return handler
                    else:
                        logger.debug(
                                '%s: %s is unexpandable; not returning it '
                                'because of a conditional',
                                self, handler)
                        continue

                elif self.no_outer and getattr(handler, "is_outer", False):
                    raise yex.exception.OuterOutOfPlaceError(
                            problem = handler.identifier,
                            )

                elif self.level<RunLevel.EXPANDING and \
                        not handler.even_if_not_expanding:
                    # don't refactor this into the other "not expanding";
                    # if it's a control or active character, we must
                    # raise an error if it's "outer", even if we're
                    # not expanding.
                    logger.debug(
                            "%s: we're not expanding; returning control: %s",
                            self, handler)
                    return handler

                elif self.doc.ifdepth[-1] or \
                        handler.conditional or \
                        handler.even_if_not_expanding:

                    # We're not prevented from executing by \if.
                    #
                    # (Or, this is one of the even_if_not_expanding controls,
                    # whose contents don't get expanded; in cases like that
                    # we have to execute but tell the control not
                    # to do anything, or the parser gets confused.
                    # See p215 of the TeXbook, and
                    # test_register_table_name_in_message().)

                    logger.debug("%s: calling %s",
                            self, handler)

                    # control exists, so run it.

                    received = handler(
                            tokens = self.another(
                                on_eof="none"),
                            )

                    logger.debug("%s: finished calling %s (%s)",
                            self, handler, type(handler))

                    if received is not None:
                        logger.debug('%s:   -- received: %s',
                                self, received)
                        return received

                else:
                    logger.debug("%s: not executing %s because "+\
                            "we're inside a conditional block",
                            self,
                            handler,
                            )

            elif isinstance(token, Internal):
                logger.debug("%s:  -- running internal token: %s",
                        self,
                        token,
                        )
                token(self)

            elif self.level<RunLevel.EXPANDING:
                logger.debug(
                        "%s: we're not expanding; returning %s",
                        self,
                        token,
                        )
                return token

            elif self.doc.ifdepth[-1]:
                logger.debug("%s:  -- returning: %s",
                        self,
                        token,
                        )
                return token
            else:
                logger.debug(
                        "%s:  -- dropping because of conditional: %s",
                        self,
                        token,
                        )

    def _next_at_executing_or_querying(self):

        assert self.level in [RunLevel.EXECUTING, RunLevel.QUERYING]

        while True:
            name = None
            item = self._source_for_next._next_at_reading_or_expanding()
            logger.debug(
                    "%s: considering %s for executing or querying",
                    self, item)

            if isinstance(item, Control):
                try:
                    v = self.doc[item.identifier]
                    logger.debug(
                            "%s:     -- ==%s (%s)",
                            self, v, type(v))
                    name = item
                    item = v
                except KeyError:
                    pass # just use the unexpanded control then

            if isinstance(item, yex.control.Control):

                if self.level>=RunLevel.QUERYING and item.is_queryable:
                    # "item" here is the array element we found if the
                    # original item was an array. Otherwise it's the
                    # original item itself.

                    logger.debug("%s:     -- a queryable control", self)

                    result = item.query(tokens=self)

                    logger.debug("%s:  -- == %s (%s); returning that",
                            self, result, type(result))
                    return result

                else:

                    logger.debug("%s:     -- an executable control", self)

                    try:
                        received = item(
                                tokens = self.another(
                                    on_eof="none"),
                                )
                    except yex.exception.YexError as ye:
                        logger.debug("%s:       -- it raised %s",
                                self, ye.__class__.__name__)
                        if item.is_queryable:
                            ye.mark_as_possible_rvalue(item)
                        raise

                if received is not None:
                    logger.debug(
                            '%s:   -- received: %s; returning that directly',
                            self, received)
                    return received

                logger.debug("%s: done calling %s; going round again",
                        self, item)

            elif self.doc.ifdepth[-1]:
                logger.debug("%s:     -- not a control; returning it", self)
                return item

            else:
                logger.debug((
                    "%s:     -- not a control; not returning it, "
                    "because we're in a False conditional"), self)

                # and round we go again

    @property
    def location(self):
        """
        The current position of this expander.

        We return the position as a named tuple with
        `filename`, `line`, and `column` fields.
        If there is no position, we return None.

        Returns:
            `source.Location`
        """
        if self.source:
            return self.source.location
        else:
            return None

    @location.setter
    def location(self, v):
        logger.debug("%s: set location: %s",
                self,
                v
                )

        if self.source:
            self.source.location = v
        else:
            raise ValueError("can't set location without a source")

    @property
    def is_expanding(self):
        r"""
        Whether this Expander is currently expanding tokens.

        If the runlevel is below EXPANDING, we are never expanding.
        If it's EXPANDING or higher, then we are expanding iff we
        are not forbidden to expand by a conditional.

        For example, even if level was EXPANDING, we wouldn't be expanding
        straight after \iffalse.
        """
        if self.level>=RunLevel.EXPANDING:
            return self.doc.ifdepth[-1]
        else:
            return False

    def push(self, thing,
            clean_char_tokens = False,
            is_result = False,
            ):
        r"""
        Pushes back a token, a character, or anything else.

        This is mostly just a wrapper for the `push` method in
        `Tokeniser`. But we do check for "beginning group"
        and "ending group" tokens, and adjust our fields accordingly.

        All Expanders share pushback, and in general it's fine to push
        things through an Expander when you received them from a
        different Expander. The only exception to this is when
        you're using balanced expansion: because we have to keep a count of
        balanced braces, you should remember to push Tokens back
        through the Expander that gave you them.

        If you push bare characters, they will be converted by the
        source as it thinks appropriate.

        If on_push is set, it will be called with three parameters
        before the push happens: this Expander, the item, and is_result.

        Args:
            thing (any): whatever you're pushing back.
                Pushing None will be ignored.
                If this is a string, or specifically a list, it
                will be split into its members and pushed in reverse order.
                For example, pushing 'cat' is the same as pushing 't',
                then pushing 'a', then pushing 'c'.

            clean_char_tokens (`bool`): if True, all bare characters
                will be converted to the Tokens for those characters.s
                (For example, 'T', 'e', 'X' -> ('T' 12) ('e' 12) ('X' 12).)
                The rules about how this is done are on p213 of the TeXbook.
                If False, the characters will remain bare characters
                and the source will tokenise them as usual when it
                gets to them.

            is_result (`bool`): If you're a control, and your job involves
                reading some data, then pushing a result, set this to True
                when you push the result. This will allow \expandafter
                to work correctly.

                If you're implemented through a decorator, and your result
                is pushed via returning it, you don't have to worry:
                the decorator will set is_result=True when it pushes your
                return values.

        Raises:
            YexError: if there is no source, because this expander
                is exhausted.

            YexError: if we're bounded, and you push more
                BEGINNING_GROUP tokens than you've already received.
        """

        if self.source is None:
            # XXX Do we ever need to use this when self.source is None?
            # XXX If yes, we should find another way to mark when we're done.
            raise yex.exception.SourceHasGoneAwayError()

        if self.on_push is not None:
            self.on_push(tokens=self, thing=thing, is_result=is_result)

        if not isinstance(thing, (str, list)):
            thing = [thing]

        if clean_char_tokens:

            def _clean(c):
                if isinstance(c, str):
                    return Token.get(
                            ch=c,
                            location=self.source.location,
                            )
                else:
                    return c

            thing = [_clean(c) for c in thing]

        self.pushback.push(thing)

        if self._bounded_limit is not None:
            if self.pushback.group_depth < self._bounded_limit:
                logger.debug(
                        '%s: group_depth is %d, but bounded_limit is %d',
                        self, self.pushback.group_depth,
                        self._bounded_limit)
                raise yex.exception.GoneBeforeTheBeginningError()

    def eat_optional_spaces(self, level='deep'):
        """
        Eats zero or more space tokens.

        This is like Tokeniser.eat_optional_spaces(), except that it can
        also execute controls and active characters, then continue to
        consider the result.

        Args:
            level: the level to run at. "deep" is the default, and will
                delegate to the tokeniser.

        Returns:
            a list of the Tokens consumed.
        """

        if level=='deep':
            return self.source.eat_optional_spaces()

        result = []
        while True:
            result.extend(self.source.eat_optional_spaces())

            t = self.next(level='querying', on_eof='none')

            if t is None:
                return result
            elif isinstance(t, Token) and t.ch in string.whitespace:
                result.append(t.ch)
            elif isinstance(t, str) and t in string.whitespace:
                result.append(t)
            else:
                self.push(t)
                return result

    def get_digit_sequence(self, accept_ch, accept_decimal_point):
        r"""
        Reads and returns a series of symbols.

        The result is taken from the next zero or more items.
        They are accepted if:
            - they are LETTER or OTHER tokens, and their "ch" property is
                in "accept_ch"; or
            - they are single-character strings, and they are in "accept_ch".

        This exists because if we read in the indexes of arrays using
        any other method, we risk \catcodeNN= affecting the way the symbol
        *after* the value which is assigned to \catcodeNN.
        See test_tokeniser_whitespace_after_control_words().

        Args:
            accept_ch (str): the characters we can accept
            accept_decimal_point (bool): if True, act as though '.,' were
                included in accept_ch, except that they can only
                be matched once.

        Returns:
            a string. Items which were tokens are represented by their
                "ch" property. Items which were strings are used directly.
        """

        DECIMAL_POINTS = '.,'
        original_accept_ch = accept_ch

        if accept_decimal_point:
            accept_ch += DECIMAL_POINTS

        logger.debug("%s: get_digit_sequence begins; accepting %s",
                self, accept_ch)

        result = ''
        exp = self.another(on_eof='none', level='expanding')

        while True:
            item = exp.next()

            if isinstance(item, (Letter, Other)) and item.ch in accept_ch:
                addendum = item.ch
                logger.debug("%s:   -- accepted token, so: %s", self, result)
            elif (isinstance(item, str) and
                    len(item)==1 and
                    item in accept_ch):
                addendum = item
                logger.debug("%s:   -- accepted char, so: %s", self, result)
            else:
                if isinstance(item, Space):
                    logger.debug("%s:   -- ending on %s, so result is: %s",
                            self, repr(item), result)
                else:
                    logger.debug((
                        "%s:   -- ending on %s (will push), "
                        "so result is: %s"),
                                 self, repr(item), result)
                    self.push(item)

                return result

            result += addendum
            if addendum in DECIMAL_POINTS:
                accept_ch = original_accept_ch

    def end(self):
        logger.debug(r'%s: we have reached an \end', self)
        self.pushback.clear()
        self.source = None

    def __repr__(self):
        result = '[exp.%04x;' % (id(self) % 0xFFFF)
        if self.bounded!='no':
            if self._bounded_limit is None:
                result += 'bounded;'
            else:
                result += 'bounded=%d;' % (self._bounded_limit)

        if self.on_eof in ['raise', 'exhaust']:
            result += self.on_eof+';'

        if self.level==RunLevel.DEEP:
            result += 'deep;'
        elif self.level==RunLevel.READING:
            result += 'read;'
        elif self.level==RunLevel.EXPANDING:
            result += 'expand;'
        elif self.level==RunLevel.EXECUTING:
            result += 'execute;'
        elif self.level==RunLevel.QUERYING:
            result += 'query;'
        else:
            result += f'?level={self.level};'

        if self.no_outer:
            result += 'no_outer;'

        if self.on_push:
            result += f'o_p={self.on_push};'

        result += repr(self.source)[5:-1]
        result += ']'
        return result
