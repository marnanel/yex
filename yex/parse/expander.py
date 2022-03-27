import logging
import yex.parse
import yex.exception
from yex.parse.tokenstream import Tokenstream
from yex.parse.tokeniser import Tokeniser

macros_logger = logging.getLogger('yex.macros')
commands_logger = logging.getLogger('yex.commands')

class _ExpanderIterator:
    def __init__(self, expander):
        self.expander = expander

    def __next__(self):
        result = self.expander.next()
        if result is None and \
                self.expander.on_eof==self.expander.EOF_EXHAUST:
            raise StopIteration
        return result

class Expander(Tokenstream):

    r"""Interprets a TeX file, and expands its macros.

    Takes a Tokeniser, and iterates over it,
    returning the tokens with the macros expanded
    according to the definitions
    stored in the Document attached to that Tokeniser.

    By default, Expander will keep returning None forever,
    which is what you want if you're planning to do
    lookahead. If you're going to put this Expander into
    a `for` loop, you'll want to set `on_eof=EOF_EXHAUST`.

    It's fine to attach another Expander to the
    same Tokeniser, and to run it even when this
    one is active.

    Attributes:
        tokeniser(`Tokeniser`): the tokeniser
        doc (`Document`): the document we're helping create.
        single (bool): if True, iteration stops after a single
            character, or after a balanced group if the
            next character is a BEGINNING_GROUP.
            If False (the default), iteration ends when the
            tokeniser ends.
        expand (bool):if True (the default), expand macros.
            If False, pass everything straight through.
            This may be adjusted mid-run.
        on_eof (`str`): one of EOF_RETURN_NONE, EOF_RAISE_EXCEPTION,
            or EOF_EXHAUST.
        no_outer (bool): if True, attempting to call a macro which
            was defined as "outer" will cause an error.
            Defaults to False.
        no_par (bool): if True, the "par" token is forbidden--
            that is, any control token whose name is `\par`.
            Defaults to False.
    """

    # Behaviours when we hit the end of the file
    # (or the string, or whatever):

    EOF_RETURN_NONE = 'none' # return None forever
    EOF_RAISE_EXCEPTION = 'raise' # raise an exception
    EOF_EXHAUST = 'exhaust' # exhaust the iterator

    def __init__(self, tokeniser,
            single = False,
            expand = True,
            on_eof = EOF_RETURN_NONE,
            no_outer = False,
            no_par = False,
            ):
        self.tokeniser = tokeniser
        self.doc = tokeniser.doc
        self.single = single
        self._single_grouping = 0
        self.expand = expand
        self.on_eof = on_eof
        self.no_outer = no_outer
        self.no_par = no_par

        # For convenience, we allow direct access to some of
        # Tokeniser's methods.
        for name in [
                'eat_optional_spaces',
                'eat_optional_equals',
                'optional_string',
                'push',
                ]:
            setattr(self, name, getattr(tokeniser, name))

        commands_logger.debug("%s: ready",
                self,
                )

    def __iter__(self):
        return _ExpanderIterator(self)

    def _read(self):
        """
        If the next thing in the stream is an active character
        token or a control token, and `expand` is True,
        we execute the control which the token names.
        We carry on doing that until we reach
        something else, at which point we return it. It might
        well be the result of whatever we executed.

        If `expand` is False, we return all the tokens
        we see, except that conditionals are honoured.

        We always honour group beginning and ending characters
        (`{` and `}` by default).

        If the next thing in the stream is none of these,
        it will be returned unchanged.

        If we go off the end of the stream: if `on_eof` is
        `EOF_RAISE_EXCEPTION`, we raise an exception.
        Otherwise, we return None.

        This method is not written as a generator because it
        needs to be recursive.
        """

        while True:

            if self.tokeniser is None or self._single_grouping==-1:
                self.tokeniser = None
                macros_logger.debug("%s: all done; returning None",
                        self)
                return None

            token = next(self.tokeniser)

            macros_logger.debug("%s: token: %s",
                    self,
                    token,
                    )

            try:
                token.category
            except AttributeError:
                # Not a token. Could be a C_ControlWord, could be some
                # other class, could be None. Anyway, it's not our problem;
                # pass it through.
                macros_logger.debug("%s  -- not a token; passing through: %s",
                        self, token,)

                if self.single and self._single_grouping==0:
                    # this was our first item, so we're done
                    self.tokeniser = None
                    macros_logger.debug("%s    -- and that's a wrap",
                            self)

                return token

            if self.no_par:
                if token.category==token.CONTROL and token.name=='par':
                    # we don't know the function name, but our caller does
                    raise yex.exception.RunawayExpansionError(None)

            if self.single and token.category!=token.INTERNAL:

                if token.category==token.BEGINNING_GROUP:
                    self._single_grouping += 1

                    if self._single_grouping==1:
                        # don't pass the opening { through
                        continue
                elif self._single_grouping==0:
                    # First token wasn't a BEGINNING_GROUP,
                    # so we handle that and then stop.
                    macros_logger.debug("%s:  -- the only symbol in a single",
                            self)
                    self._single_grouping = -1
                    # ...and go round to the -1 case above
                elif token.category==token.END_GROUP:
                    self._single_grouping -= 1
                    if self._single_grouping==0:
                        macros_logger.debug("%s:  -- the last } in a single",
                                self)
                        self.tokeniser = None
                        continue

            if token.category in (token.CONTROL, token.ACTIVE):

                name = token.identifier

                if self.expand:
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
                    macros_logger.debug(
                            r"\%s doesn't exist; returning it",
                            token)
                    return token

                elif isinstance(handler, yex.control.C_Unexpandable):
                    macros_logger.debug('%s is unexpandable; returning it', handler)
                    return token

                elif self.no_outer and handler.is_outer:
                    raise yex.exception.MacroError(
                            "outer macro called where it shouldn't be")

                elif not self.expand and not isinstance(
                        handler, yex.control.C_StringControl):
                    # don't refactor this into the other "not expand";
                    # if it's a control or active character, we must
                    # raise an error if it's "outer", even if we're
                    # not expanding.
                    macros_logger.debug(
                            "%s: we're not expanding; returning control token",
                            token)
                    return token

                elif self.doc.ifdepth[-1] or isinstance(
                        handler, yex.control.C_StringControl):
                    # We're not prevented from executing by \if.
                    #
                    # (Or, this is one of those special macros like \message
                    # which don't expand their contents; in cases like that
                    # we have to execute but tell the macro not to do anything,
                    # or the parser gets confused. See p215 of the TeXbook, and
                    # test_register_table_name_in_message().)

                    commands_logger.debug("%s: calling %s",
                            self, handler)

                    # control exists, so run it.
                    if isinstance(handler, yex.control.C_StringControl):
                        commands_logger.debug(
                                "%s:   -- special case, string macro",
                                handler,
                                )

                        if self.expand:
                            expand = self.doc.ifdepth[-1]
                        else:
                            expand = False

                        handler(
                                name = token,
                                tokens = self.child(on_eof=self.EOF_RETURN_NONE),
                                expand = expand,
                                )

                    elif isinstance(handler, yex.control.Noexpand):
                        token2 = self.next(deep=True)
                        commands_logger.debug(
                                r"%s: not expanding %s",
                                token, token2)
                        return token2

                    else:
                        handler(
                                name = token,
                                tokens = self.child(on_eof=self.EOF_RETURN_NONE),
                                )

                else:
                    commands_logger.debug("%s: not executing %s because "+\
                            "we're inside a conditional block",
                            self,
                            handler,
                            )

            elif token.category==token.INTERNAL:
                commands_logger.debug("%s:  -- running internal token: %s",
                        self,
                        token,
                        )
                token(token, self)

            elif not self.expand:
                macros_logger.debug(
                        "%s: we're not expanding; returning %s",
                        self,
                        token,
                        )
                return token

            elif token.category in (
                    token.BEGINNING_GROUP,
                    token.END_GROUP,
                    ):
                commands_logger.debug("%s:  -- returning group delimiter: %s",
                        self,
                        token,
                        )
                return token

            elif self.doc.ifdepth[-1]:
                commands_logger.debug("%s:  -- returning: %s",
                        self,
                        token,
                        )
                return token
            else:
                commands_logger.debug(
                        "%s:  -- dropping because of conditional: %s",
                        self,
                        token,
                        )

    def child(self, **kwargs):
        """
        Returns another expander, with given changes to its behaviour.

        The result will be a new Expander on the same Tokeniser.
        Any setting specified in `kwargs` will be honoured.
        `single` will switch back to False if it's not in `kwargs`;
        all other settings will be copied from this Expander.

        Returns:
            `Expander`
        """
        commands_logger.debug(
                "%s: spawning a child Expander with changes: %s",
                self,
                kwargs)

        params = {
                'tokeniser': self.tokeniser,
                'single': False,
                'expand': self.expand,
                'on_eof': self.on_eof,
                'no_outer': self.no_outer,
                'no_par': self.no_par,
                }
        params |= kwargs

        result = Expander(**params)
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
        return self.child(
                single=True,
                on_eof=self.EOF_EXHAUST,
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
        return self.child(expand=True, **kwargs)

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
        return self.child(expand=False, **kwargs)

    def next(self,
            expand = None,
            on_eof = None,
            no_outer = None,
            no_par = None,
            deep = False,
            ):
        r"""
        Returns a single token.

        This is just like next() on an iterator, but with more options.

        Args:
            expand (bool): if True, expand this token as necessary.
                If False, don't expand this token.
                If unspecified, go with the defaults for
                this Expander.
            on_eof (str):  what to do if it's the end of the file.
                `EOF_EXHAUST` is treated like `EOF_RETURN_NONE`.
                If unspecified, go with the defaults for
                this Expander.
            no_par (bool): if True, finding `\par` will cause an error.
            no_outer (bool): if True, finding an outer macro will cause
                an error.
            deep (bool): If True, the token is taken from
                the tokeniser rather than the expander.
                This allows you to see characters that
                would ordinarily be interpreted
                before you got to them.
                This option ignores the value of expand,
                because a tokeniser doesn't expand anyway.

        Raises:
            `ParseError` on unexpected end of file, or if `no_par`
            or `no_outer` find the appropriate problems.

        Returns:
            `Token`
        """

        restore = {}

        for field in ['expand', 'on_eof', 'no_outer', 'no_par']:
            whether = locals()[field]
            if whether is None:
                continue
            restore[field] = getattr(self, field)
            setattr(self, field, whether)

        if deep:
            result = next(self.tokeniser)
        else:
            result = self._read()

        if result is None and self.on_eof==self.EOF_RAISE_EXCEPTION:
            # This is usually already caught, but might not have
            # been if deep=True
            raise yex.exception.ParseError("unexpected EOF")

        for f,v in restore.items():
            setattr(self, f, v)

        return result

    def __repr__(self):
        result = '[exp.%04x=' % (id(self) % 0xFFFF)
        if self.single:
            result += 'S%d' % (self._single_grouping)

        if self.on_eof==self.EOF_RAISE_EXCEPTION:
            result += '*'
        elif self.on_eof==self.EOF_EXHAUST:
            result += 'X'

        if self.expand:
            result += 'E'
        if self.no_outer:
            result += 'O'
        if self.no_par:
            result += 'P'
        result += ';'

        result += repr(self.tokeniser)[1:-1].replace('tok;','')
        result += ']'
        return result
