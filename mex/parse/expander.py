import logging
import mex.parse
import mex.exception
from mex.parse.tokenstream import Tokenstream
from mex.parse.tokeniser import Tokeniser

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')

class _ExpanderIterator:
    def __init__(self, expander):
        self.expander = expander

    def __next__(self):
        result = self.expander.next()
        if result is None and \
                self.expander.on_eof==self.expander.EOF_EXHAUST:
            raise StopIteration
        return result

class InfiniteExpander(Tokenstream):

    r"""
    Takes a Tokeniser, and iterates over it,
    returning the tokens with the macros expanded
    according to the definitions
    stored in the State attached to that Tokeniser.

    InfiniteExpander will keep returning None forever,
    which is what you want if you're planning to do
    lookahead. There is a subclass called Expander
    which will exhaust when it reaches the end of the file.
    But even Expanders will always spawn InfiniteExpanders.

    It's fine to attach another Expander to the
    same Tokeniser, and to run it even when this
    one is active.

    Parameters:
        tokeniser - the Tokeniser
        single  -   if True, iteration stops after a single
                    character, or a balanced group if the
                    next character is a BEGINNING_GROUP.
                    If False (the default), iteration ends when the
                    Tokeniser ends.
        on_eof -    one of EOF_RETURN_NONE, EOF_RAISE_EXCEPTION,
                    or EOF_EXHAUST. These are described below.
        expand -    if True (the default), expand macros.
                    If False, pass everything straight through.
                    This may be adjusted mid-run.
        no_outer -  if True, attempting to call a macro which
                    was defined as "outer" will cause an error.
                    Defaults to False.
        no_par -    if True, the "par" token is forbidden--
                    that is, any control whose name is "\par".
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
        """
        See the description of the Expander class for the parameters.
        """

        self.tokeniser = tokeniser
        self.state = tokeniser.state
        self.single = single
        self.single_grouping = 0
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
        token or a control token, and self.expand is True,
        we execute the control which the token names.
        We carry on doing that until we reach
        something else, at which point we return it. It might
        well be the result of whatever we executed.

        If self.expand is False, we return all the tokens
        we see, except that conditionals are honoured.

        We always honour group beginning and ending characters
        ("{" and "}" by default).

        If the next thing in the stream is none of these,
        it will be returned unchanged.

        If we go off the end of the stream: if on_eof is
        EOF_RAISE_EXCEPTION, we raise an exception.
        Otherwise, we return None.

        This method is not written as a generator because it
        needs to be recursive.
        """

        while True:

            if self.tokeniser is None:
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
                return token

            if self.no_par:
                if token.category==token.CONTROL and token.name=='par':
                    raise mex.exception.ParseError(
                            "runaway expansion")

            if self.single and token.category!=token.INTERNAL:

                if self.single_grouping==-1:
                    # self.single was set, and the first token wasn't
                    # a BEGINNING_GROUP, so we're just passing one token
                    # through. And we just returned that token, so we're done.
                    self.push(token)
                    self.tokeniser = None
                    return None

                elif token.category==token.BEGINNING_GROUP:
                    self.single_grouping += 1

                    if self.single_grouping==1:
                        # don't pass the opening { through
                        continue
                elif self.single_grouping==0:
                    # First token wasn't a BEGINNING_GROUP,
                    # so we handle that and then stop.
                    macros_logger.debug("%s:  -- the only symbol in a single",
                            self)
                    self.single_grouping = -1
                    # ...and go round to the -1 case above
                elif token.category==token.END_GROUP:
                    self.single_grouping -= 1
                    if self.single_grouping==0:
                        macros_logger.debug("%s:  -- the last } in a single",
                                self)
                        self.tokeniser = None
                        continue

            if token.category in [token.CONTROL, token.ACTIVE]:

                try:
                    name = token.name
                except AttributeError:
                    name = token.ch

                if self.expand:
                    handler = self.state.get(name,
                            default=None,
                            tokens=self)
                else:
                    # If we supply "tokens", State will try to do the
                    # lookup on things like \count100, which will
                    # consume "100".
                    handler = self.state.get(name,
                            default=None,
                            tokens=None)

                if handler is None:
                    macros_logger.debug(
                            r"\%s doesn't exist; returning it",
                            token)
                    return token

                elif isinstance(handler, mex.control.C_Unexpandable):
                    macros_logger.debug('%s is unexpandable; returning it', handler)
                    return token

                elif self.no_outer and handler.is_outer:
                    raise mex.exception.MacroError(
                            "outer macro called where it shouldn't be")

                elif not self.expand and not isinstance(
                        handler, mex.control.C_StringControl):
                    # don't refactor this into the other "not expand";
                    # if it's a control or active character, we must
                    # raise an error if it's "outer", even if we're
                    # not expanding.
                    macros_logger.debug(
                            "%s: we're not expanding; returning control token",
                            token)
                    return token

                elif self.state.ifdepth[-1] or isinstance(
                        handler, mex.control.C_StringControl):
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
                    if isinstance(handler, mex.control.C_StringControl):
                        commands_logger.debug(
                                "%s:   -- special case, string macro",
                                handler,
                                )

                        if self.expand:
                            expand = self.state.ifdepth[-1]
                        else:
                            expand = False

                        handler(
                                name = token,
                                tokens = self.child(on_eof=self.EOF_RETURN_NONE),
                                expand = expand,
                                )

                    elif isinstance(handler, mex.control.Noexpand):
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
                return token

            elif self.state.ifdepth[-1]:
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
        Returns an InfiniteExpander on the same Tokeniser,
        with the settings as follows:

           - Any setting specified in kwargs will be honoured.
           - Single will switch back to False.
           - All other settings will be copied from this Expander.
        """
        commands_logger.debug(
                "%s: spawning a child InfiniteExpander with changes: %s",
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

        result = InfiniteExpander(**params)
        return result

    def single_shot(self, **kwargs):
        return self.child(
                single=True,
                on_eof=self.EOF_EXHAUST,
                **kwargs)

    def expanding(self, **kwargs):
        return self.child(expand=True, **kwargs)

    def not_expanding(self, **kwargs):
        return self.child(expand=False, **kwargs)

    def next(self,
            expand = None,
            on_eof = None,
            no_outer = None,
            no_par = None,
            deep = False,
            ):
        r"""
        Returns a single token, just like next()
        on an iterator, but with more options:

        expand -        if True, expand this token as necessary
                        If False, don't expand this token.
                        If unspecified, go with the defaults for
                        this InfiniteExpander.
        on_eof -        what to do if it's the end of the file.
                        EOF_EXHAUST is treated like EOF_RETURN_NONE.
                        If unspecified, go with the defaults for
                        this InfiniteExpander.
        no_par -        if True, finding "\par" will cause an error.
        no_outer -      if True, finding an outer macro will cause an error.
        deep -          If True, the token is taken from
                        the tokeniser rather than the Expander.
                        This allows you to see characters that
                        would ordinarily be interpreted
                        before you got to them.
                        This option ignores the value of expand,
                        because a tokeniser doesn't expand anyway.
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
            # This is usually already caught, but might not have been
            # if deep=True
            raise mex.exception.ParseError("unexpected EOF")

        for f,v in restore.items():
            setattr(self, f, v)

        return result

    def __repr__(self):
        result = '[exp.%04x=' % (id(self) % 0xFFFF)
        if self.single:
            result += 'S%d' % (self.single_grouping)

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

class Expander(InfiniteExpander):
    """
    Like InfiniteExpander, except that the on_eof defaults to EOF_EXHAUST.
    """

    def __init__(self, *args, **kwargs):
        if 'on_eof' not in kwargs:
            kwargs['on_eof'] = self.EOF_EXHAUST

        super().__init__(*args, **kwargs)
