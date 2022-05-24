import logging
import enum
import yex.exception
import yex.util
from yex.parse.tokeniser import *
from yex.parse.token import *

logger = logging.getLogger('yex.general')

class _ExpanderIterator:
    def __init__(self, expander):
        self.expander = expander

    def __next__(self):
        result = self.expander.next()
        if result is None and \
                self.expander.on_eof=="exhaust":
            raise StopIteration
        return result

class RunLevel(enum.IntEnum):
    r"""
    Levels you can run an Expander at.

    Attributes:
        DEEP: direct access to the tokeniser beneath.
            For example, this will emit group delimiters
            rather than using them to start or end groups.
            This can only be used with next(), rather than
            with iterators, and you probably don't want to use it.

        READING: the expander will handle most kinds of
            token for you. But it will emit all control tokens,
            whether expandable or unexpandable, as well as
            all active tokens, all registers, and all LETTERs and OTHERs.
            This is the lowest level in common use.

        EXPANDING: like READING, except that the expander will
            only return control tokens for unexpandable controls.
            It will run any expandable controls for you.
            For example, you won't see any of the symbols
            between \iffalse and \fi, and you won't see any
            user-defined macros.

        EXECUTING: like EXPANDING, except that unexpandable controls,
            active tokens, and registers will be run rather than emitted.
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
        raise yex.exception.ParseError(
                f"internal error: {name} is not a run level")

EOF_OPTIONS = set(('none', 'raise', 'exhaust'))

class Expander(Tokenstream):

    r"""Interprets a TeX file, and expands its macros.

    Takes a tokeniser, and iterates over it,
    returning the tokens with the macros expanded
    according to the definitions
    stored in the Document attached to that tokeniser.

    By default, Expander will keep returning None forever,
    which is what you want if you're planning to do
    lookahead. If you're going to put this Expander into
    a `for` loop, you'll want to set `on_eof="exhaust"`.

    It's fine to attach another Expander to the
    same tokeniser, and to run it even when this
    one is active.

    Attributes:
        tokeniser(`Tokeniser`): the tokeniser
        doc (`yex.Document`): the document we're helping create.
        single (bool): if True, iteration stops after a single
            character, or after a balanced group if the
            next character is a BEGINNING_GROUP.
            If False (the default), iteration ends when the
            tokeniser ends.
        level (`RunLevel` or `str`): the level to run at;
            see the documentation for RunLevel for further information.
            Default is 'executing'.
        on_eof (`str`): what to do if we reach the end of the file.
            Use `"none"` to return `None` forever, `"raise"` to
            raise `ParseError`, or `"exhaust"` to exhaust the iterator.
        no_outer (bool): if True, attempting to call a macro which
            was defined as "outer" will cause an error.
            Defaults to False.
        no_par (bool): if True, the "par" token is forbidden--
            that is, any control token whose name is `\par`.
            Defaults to False.
    """

    def __init__(self, tokeniser,
            single = False,
            level = RunLevel.EXECUTING,
            on_eof = 'none',
            no_outer = False,
            no_par = False,
            ):
        self.tokeniser = tokeniser
        self.doc = tokeniser.doc
        self.single = single
        self._single_grouping = 0
        self.level = _runlevel_by_name(level)
        self.on_eof = on_eof
        self.no_outer = no_outer
        self.no_par = no_par

        # For convenience, we allow direct access to some of
        # Tokeniser's methods.
        for name in [
                'eat_optional_spaces',
                'eat_optional_equals',
                'optional_string',
                'error_position',
                ]:
            setattr(self, name, getattr(tokeniser, name))

        logger.debug("%s: ready; called from %s",
                self,
                yex.util.show_caller,
                )

    def __iter__(self):
        return _ExpanderIterator(self)

    def _read(self):
        """
        Finds the next item in the input.

        Honours self.level. See `RunLevel` for what that means.
        `EXECUTING` is accomplished by callers of this method,
        not within this method itself.

        If we go off the end of the stream: if `self.on_eof` is
        `"raise"`, we raise an exception.
        Otherwise, we return None.

        This method is not written as a generator because it
        needs to be recursive.
        """

        while True:

            if self.tokeniser is None or self._single_grouping==-1:
                self.tokeniser = None
                logger.debug("%s: all done; returning None",
                        self)
                return None

            token = next(self.tokeniser)

            logger.debug("%s: token: %s",
                    self,
                    token,
                    )

            try:
                token.category
            except AttributeError:
                # Not a token. Could be a C_Control, could be some
                # other class, could be None. Anyway, it's not our problem;
                # pass it through.
                if self.doc.ifdepth[-1]:
                    logger.debug("%s  -- not a token; "
                            "passing through: %s",
                            self, token,)

                    return token
                else:
                    logger.debug("%s  -- not passing %s because "
                            "of a conditional",
                            self, token)
                    continue

            if self.no_par:
                if isinstance(token, Control) and token.name=='par':
                    # we don't know the function name, but our caller does
                    raise yex.exception.RunawayExpansionError(None)

            if isinstance(token, (Control, yex.parse.Active)):

                name = token.identifier

                if self.level >= RunLevel.EXPANDING:
                    handler = self.doc.get(name,
                            default=None,
                            tokens=self)
                else:
                    # If we supply "tokens", Document will try to do the
                    # lookup on things like \count100, which will
                    # consume "100".
                    handler = self.doc.get(name,
                            default=None,
                            tokens=None)

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

                elif not isinstance(handler, yex.control.C_Expandable):
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

                elif self.no_outer and handler.is_outer:
                    raise yex.exception.MacroError(
                            "outer macro called where it shouldn't be")

                elif self.level<RunLevel.EXPANDING and not isinstance(
                        handler, yex.control.C_StringControl):
                    # don't refactor this into the other "not expanding";
                    # if it's a control or active character, we must
                    # raise an error if it's "outer", even if we're
                    # not expanding.
                    logger.debug(
                            "%s: we're not expanding; returning control: %s",
                            self, handler)
                    return handler

                elif self.doc.ifdepth[-1] or isinstance(
                        handler, (
                            yex.control.C_StringControl,
                            yex.control.C_Conditional,
                            )):

                    # We're not prevented from executing by \if.
                    #
                    # (Or, this is one of those special controls like \message
                    # which don't expand their contents; in cases like that
                    # we have to execute but tell the control not
                    # to do anything, or the parser gets confused.
                    # See p215 of the TeXbook, and
                    # test_register_table_name_in_message().)

                    logger.debug("%s: calling %s",
                            self, handler)

                    # control exists, so run it.
                    if isinstance(handler, yex.control.C_StringControl):
                        logger.debug(
                                "%s:   -- %s: special case, string control",
                                self, handler,
                                )

                        if self.level>=RunLevel.EXPANDING:
                            expand = self.doc.ifdepth[-1]
                        else:
                            expand = False

                        result = handler(
                                tokens = self.another(
                                    on_eof="none"),
                                expand = expand,
                                )

                        if result is not None:
                            logger.debug(
                                    "%s:   -- %s returned %s; "
                                    "passing it through",
                                    self, handler, result,
                                    )

                            return result

                    elif isinstance(handler, yex.control.Noexpand):
                        token2 = self.next(level='deep')
                        logger.debug(
                                r"%s: not expanding %s",
                                token, token2)
                        return token2

                    else:
                        handler(
                                tokens = self.another(
                                    on_eof="none"),
                                )
                    logger.debug("%s: finished calling %s",
                            self, handler)

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

    def another(self, **kwargs):
        """
        Returns another expander, with given changes to its behaviour.

        The result will be a new Expander on the same Tokeniser.
        Any setting specified in `kwargs` will be honoured.
        `single` will switch back to False if it's not in `kwargs`;
        all other settings will be copied from this Expander.

        Returns:
            `Expander`
        """
        our_params = {
                'tokeniser': self.tokeniser,
                'single': False,
                'level': self.level,
                'on_eof': self.on_eof,
                'no_outer': self.no_outer,
                'no_par': self.no_par,
                }
        new_params = our_params | kwargs

        if our_params==new_params:
            logger.debug(
                    "%s: not spawning another Expander; no changes requested",
                    self,
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

    def single_shot(self, **kwargs):
        """
        Returns a new expander for interpreting a single item.

        The new expander will yield a single symbol, unless that
        symbol begins a group. In that case, it will keep yielding
        symbols until it's found a balanced set of brackets. In either case,
        it will then be exhausted.

        Args:
            kwargs: other settings for the new expander's constructor.

        Returns:
            `Expander`
        """
        return self.another(
                single=True,
                on_eof="exhaust",
                **kwargs)

    def expanding(self, **kwargs):
        """
        Returns a new expander, like this one, but with expanding turned on.

        You can use this even if the current expander is already expanding.

        Args:
            kwargs: other settings for the new expander's constructor.

        Returns:
            `Expander`
        """
        return self.another(level=RunLevel.EXPANDING, **kwargs)

    def not_expanding(self, **kwargs):
        """
        Returns a new expander, like this one, but with expanding turned off.

        You can use this even if the current expander is already
        not expanding.

        Args:
            kwargs: other settings for the new expander's constructor.

        Returns:
            `Expander`
        """
        return self.another(level=RunLevel.EXECUTING, **kwargs)

    def _read_until_non_control(self):
        """
        Ancillary to next().
        """
        while True:
            name = None
            item = self._read()

            if isinstance(item, Control):
                try:
                    v = self.doc[item.identifier]
                    logger.debug(
                            "%s: next() found %s, ==%s",
                            self, item, v)
                    name = item
                    item = v
                except KeyError:
                    pass # just return the unexpanded control then

            if isinstance(item, (
                yex.control.C_Control,
                yex.register.Register,
                )):

                if self.level==RunLevel.QUERYING:
                    if 'value' in dir(item):
                        logger.debug((
                            "%s: next() found control with a value; "
                            "returning it: %s"),
                            self, item)
                        return item

                logger.debug((
                        "%s: next() found control; going round again: "
                        "%s, of type %s"),
                        self, item, type(item))

                item(tokens=self)

            elif self.doc.ifdepth[-1]:
                logger.debug(
                        "%s: next() found non-control; returning it: %s",
                        self, item)

                return item
            else:
                logger.debug((
                        "%s: next() found non-control; "
                        "not returning it, because of conditional: %s"
                        ),
                        self, item)
                # and round we go again

    def next(self,
            level = None,
            on_eof = None,
            no_outer = None,
            no_par = None,
            ):
        r"""
        Returns a single item.

        This is just like next() on an iterator, but with more options.
        (And indeed, our iterators are implemented in terms of this method.)

        Args:
            level (RunLevel): see the documentation for `RunLevel`.
                If unspecified, go with the defaults for
                this Expander.
            on_eof (str):  what to do if it's the end of the file.
                `"exhaust"` is treated like `"none"`.
                If unspecified, go with the defaults for
                this Expander.
            no_par (bool): if True, finding `\par` will cause an error.
            no_outer (bool): if True, finding an outer macro will cause
                an error.

        Raises:
            `ParseError` on unexpected end of file, or if `no_par`
            or `no_outer` find the appropriate problems.

        Returns:
            `Token`
        """
        restore = {}

        level = _runlevel_by_name(level)

        for field in ['on_eof', 'no_outer', 'no_par', 'level']:
            whether = locals()[field]
            if whether is None:
                continue
            restore[field] = getattr(self, field)
            setattr(self, field, whether)

        if self.level<=RunLevel.DEEP:
            result = next(self.tokeniser)
        elif self.level>=RunLevel.EXECUTING:
            result = self._read_until_non_control()
        else:
            # _read() can handle the difference between
            # READING and EXECUTING itself.
            result = self._read()

        logger.debug("%s: -- found %s",
                self, result)

        if self.single:

            if isinstance(result, BeginningGroup):
                self._single_grouping += 1

                if self._single_grouping==1:
                    # don't pass the opening { through
                    logger.debug("%s:  -- opens single, read again",
                            self)
                    result = self.next()

            elif self._single_grouping==0:
                # First result wasn't a BEGINNING_GROUP,
                # so we handle that and then stop.
                logger.debug("%s:  -- the only symbol in a single",
                        self)
                self.tokeniser = None

            elif isinstance(result, EndGroup):
                self._single_grouping -= 1
                if self._single_grouping==0:
                    logger.debug("%s:  -- the last } in a single",
                            self)
                    self.tokeniser = None
                    result = None

        if result is None and self.on_eof=="raise":
            # This is usually already caught, but might not have
            # been if level==DEEP
            raise yex.exception.ParseError("unexpected EOF")

        for f,v in restore.items():
            setattr(self, f, v)

        return result

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
        if self.tokeniser:
            return self.tokeniser.location
        else:
            return None

    @location.setter
    def location(self, v):
        logger.debug("%s: set location: %s",
                self,
                v
                )

        if self.tokeniser:
            self.tokeniser.location = v
        else:
            raise ValueError("can't set location without a tokeniser")

    def push(self, thing,
            clean_char_tokens = False):
        """
        Pushes back a token, a character, or anything else.

        This is mostly just a wrapper for the `push` method in
        `Tokeniser`. But we do check for "beginning group"
        and "ending group" tokens, and adjust our fields accordingly.

        All Expanders share pushback, and in general it's fine to push
        things through an Expander when you received them from a
        different Expander. The only exception to this is when
        you're using single=True: because we have to keep a count of
        balanced braces, you should remember to push Tokens back
        through the Expander that gave you them.

        If you push bare characters, they will be converted by the
        tokeniser as it thinks appropriate.

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
                and the tokeniser will tokenise them as usual when it
                gets to them.

        Raises:
            YexError: if there is no tokeniser, because this expander
                is exhausted.

            YexError: if we're in single mode, and you push more
                BEGINNING_GROUP tokens than you've already received.
        """

        if self.tokeniser is None:
            # XXX Do we ever need to use this when self.tokeniser is None?
            # XXX If yes, we should find another way to mark when we're done.
            raise yex.exception.YexError(
                    "the tokeniser has gone away now")

        if self.single and isinstance(thing, Token):

            if isinstance(thing, BeginningGroup):
                self._single_grouping -= 1

                if self._single_grouping <= 0:
                    raise yex.exception.YexError(
                            "you have gone back before the beginning")

        self.tokeniser.push(thing, clean_char_tokens)

    def __repr__(self):
        result = '[exp.%04x;' % (id(self) % 0xFFFF)
        if self.single:
            result += 'single=%d;' % (self._single_grouping)

        if self.on_eof in ['raise', 'exhaust']:
            result += self.on_eof+';'

        if self.level==RunLevel.EXPANDING:
            result += 'expand;'
        elif self.level==RunLevel.EXECUTING:
            result += 'execute;'
        if self.no_outer:
            result += 'no_outer;'
        if self.no_par:
            result += 'no_par;'

        result += repr(self.tokeniser)[5:-1]
        result += ']'
        return result
