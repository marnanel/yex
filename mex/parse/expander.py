import logging
import mex.parse
import mex.exception

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')

class Expander:

    """
    Takes a Tokeniser, and iterates over it,
    yielding the tokens with the macros expanded
    according to the definitions
    stored in the State attached to that Tokeniser.

    It's fine to attach another Expander to the
    same Tokeniser, and to run it even when this
    one is in the middle of a yield.

    Parameters:
        tokens  -   the Tokeniser
        single  -   if True, iteration stops after a single
                    character, or a balanced group if the
                    next character is a BEGINNING_GROUP.
                    If False (the default), iteration ends when the
                    Tokeniser ends.
        running -   if True (the default), expand macros.
                    If False, pass everything straight through.
                    This may be adjusted mid-run.
        allow_eof - if True (the default), end iteration at
                    the end of the file.
                    If False, continue returning None forever.
        no_outer -  if True, attempting to call a macro which
                    was defined as "outer" will cause an error.
                    Defaults to False.
        no_par -    if True, the "par" token is forbidden--
                    that is, any control whose name is "\\par",
                    not necessarily our own Par class.
                    Defaults to False.
    """

    def __init__(self, tokens,
            single = False,
            running = True,
            allow_eof = True,
            no_outer = False,
            no_par = False,
            ):

        self.tokens = tokens
        self.state = tokens.state
        self.single = single
        self.single_grouping = 0
        self.running = running
        self.allow_eof = allow_eof
        self.no_outer = no_outer
        self.no_par = no_par

        self._iterator = self._read()

    def __iter__(self):
        return self

    def __next__(self):
        return self._iterator.__next__()

    def _read(self):

        while True:

            try:
                token = self.tokens.__next__()
            except StopIteration:

                if self.tokens.push_back:
                    token = self.tokens.push_back.pop()
                elif self.allow_eof:
                    return
                else:
                    token = None

            macros_logger.debug("token: %s", token)

            if self.no_par:
                if token.category==token.CONTROL and token.name=='par':
                    raise mex.exception.ParseError(
                            "runaway expansion")

            if self.single:

                if self.single_grouping==-1:
                    # self.single was set, and the first token wasn't
                    # a BEGINNING_GROUP, so we're just passing one token
                    # through. And we just yielded that token, so we're done.
                    self.push(token)
                    return
                elif token.category==token.BEGINNING_GROUP:
                    self.single_grouping += 1

                    macros_logger.debug("single_grouping now %d", self.single_grouping)
                    if self.single_grouping==1:
                        # don't pass the opening { through
                        continue
                elif self.single_grouping==0:
                    # First token wasn't a BEGINNING_GROUP,
                    # so we yield that and then stop.
                    macros_logger.debug("  -- the only symbol in a single")
                    self.single_grouping = -1
                elif token.category==token.END_GROUP:
                    self.single_grouping -= 1
                    if self.single_grouping==0:
                        macros_logger.debug("  -- the last } in a single")
                        return

            if not self.running:
                yield token

            elif token is None:
                yield token

            elif token.category==token.BEGINNING_GROUP:
                self.state.begin_group()

            elif token.category==token.END_GROUP:
                try:
                    self.state.end_group()
                except ValueError as ve:
                    raise mex.exception.ParseError(
                            str(ve))

            elif token.category in [token.CONTROL, token.ACTIVE]:

                try:
                    name = token.name
                except AttributeError:
                    name = token.ch

                handler = self.state.get(name,
                        default=None,
                        tokens=self.tokens)

                if handler is None:
                    macros_logger.debug(
                            r"\%s doesn't exist; yielding it",
                            token.name)
                    yield token

                elif isinstance(handler, mex.control.C_Conditional):
                    macros_logger.debug('Calling conditional: %s', handler)
                    handler(name=token, tokens=self.tokens)

                elif self.no_outer and handler.is_outer:
                    raise mex.exception.MacroError(
                            "outer macro called where it shouldn't be")

                elif self.state.ifdepth[-1] or isinstance(
                        handler, mex.control.C_StringMacro):
                    # We're not prevented from executing by \if.
                    #
                    # (Or, this is one of those special macros like \message
                    # which don't expand their contents; in cases like that
                    # we have to execute but tell the macro not to do anything,
                    # or the parser gets confused. See p215 of the TeXbook, and
                    # test_register_table_name_in_message().)

                    commands_logger.debug("%s: calling %s",
                            self.state.mode, handler)

                    # control exists, so run it.
                    if isinstance(handler, mex.control.C_StringMacro):
                        handler_result = handler(
                                name = token,
                                tokens = self.tokens,
                                running = self.state.ifdepth[-1],
                                )
                    else:
                        handler_result = handler(
                                name = token,
                                tokens = self.tokens,
                                )
                    macros_logger.debug('  -- with result: %s', handler_result)

                    if isinstance(handler, mex.control.Noexpand):
                        commands_logger.debug(
                                r"  -- yielding \noexpand token: %s",
                                handler_result)
                        yield handler_result
                    elif handler_result:
                        self.tokens.push(handler_result)
                else:
                    commands_logger.debug("Not executing %s because "+\
                            "we're inside a conditional block",
                            handler)

            elif self.state.ifdepth[-1]:
                yield token

    def push(self, token):

        if token is None:
            return

        self.tokens.push(token)

    def __repr__(self):
        result = '[Expander;flags='
        if self.single:
            result += 'S%d' % (self.single_grouping)
        if not self.running:
            result += 'R'
        if self.allow_eof:
            result += 'A'
        if self.no_outer:
            result += 'O'
        if self.no_par:
            result += 'P'
        result += ';'

        result += repr(self.tokens)[1:-1].replace('Tokeniser;','')
        result += ']'
        return result

    def error_position(self, *args, **kwargs):
        return self.tokens.error_position(*args, **kwargs)
