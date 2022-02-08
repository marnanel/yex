import logging
import mex.token
import mex.value
import mex.exception
import sys

macro_logger = logging.getLogger('mex.macros')
command_logger = logging.getLogger('mex.commands')

# XXX Most of this is to do with controls rather than macros
# XXX Split it out.

class Macro:

    def __init__(self,
            is_long = False,
            is_outer = False,
            name = None,
            *args, **kwargs):

        self.is_long = is_long
        self.is_outer = is_outer

        if name is None:
            self.name = self.__class__.__name__.lower()
        else:
            self.name = name

    def __call__(self, name, tokens):
        raise ValueError("superclass does nothing useful in itself")

    def __repr__(self):
        return f'[\\{self.name}]'

class _UserDefined(Macro):

    def __init__(self,
            definition,
            params,
            *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.definition = definition
        self.params = params

    def __call__(self, name, tokens):

        # Try to find values for our params.
        parameter_values = {}
        i = 0
        current_parameter = None

        through_possible_param_end = 0

        p = self.params

        while i<len(self.params):

            if p[i].category == p[i].PARAMETER:

                current_parameter = p[i].ch
                parameter_values[current_parameter] = []
                i += 1

                # If this parameter is immediately followed by another
                # parameter (or the end of the parameters), then the
                # value is either only one character
                # or a grouping in braces.

                if i>=len(self.params) or p[i].category==p[i].PARAMETER:

                    e = Expander(tokens,
                            single=True,
                            no_outer=True,
                            no_par=not self.is_long,
                            )
                    for token in e:

                        parameter_values[current_parameter].append(token)

                continue

            # So, not a parameter.
            raise ValueError('(not yet implemented)') # TODO

        interpolated = []
        for t in self.definition:
            if t.category==t.PARAMETER:
                for t2 in parameter_values[t.ch]:
                    interpolated.append(t2)
            else:
                interpolated.append(t)

        result = []
        for token in Expander(
                mex.token.Tokeniser(
                    state = tokens.state,
                    source = interpolated,
                    ),
                no_outer = True,
                ):
            result.append(token)

        return result

    def __repr__(self):
        result = f'[\\{self.name}:'

        if self.params:
            result += '('
            for c in self.params:
                result += str(c)
            result += ')'

        for c in self.definition:
            result += str(c)

        result += ']'
        return result

class Def(Macro):

    def __call__(self, name, tokens,
        is_global = False,
        is_outer = False,
        is_long = False,
        is_expanded = False,
        ):

        # Optional arguments may be supplied by Outer,
        # below.

        token = tokens.__next__()
        macro_logger.info("defining new macro:")
        macro_logger.info("  -- macro name: %s", token)

        if token.category==token.CONTROL:
            macro_name = token.name
        elif token.category==token.ACTIVE:
            macro_name = token.ch
        else:
            raise mex.exception.ParseError(
                    f"definition names must be "+\
                            f"a control sequence or an active character" +\
                            f"(not {token})",
                            tokens)

        params = []

        for token in tokens:
            macro_logger.debug("  -- param token: %s", token)
            if token.category == token.BEGINNING_GROUP:
                tokens.push(token)
                break
            elif token.category == token.CONTROL and \
                    tokens.state.controls[token.name].is_outer:
                        raise mex.exception.ParseError(
                                "outer macros not allowed in param lists",
                                tokens.state)
            else:
                # TODO check that params are in the correct order
                # (per TeXbook)
                params.append(token)

        macro_logger.info("  -- params: %s", params)

        # now the definition
        definition = []

        for token in Expander(tokens,
                running=is_expanded,
                single=True,
                no_outer=True,
                ):
            macro_logger.debug("  -- definition token: %s", token)
            definition.append(token)

        new_macro = _UserDefined(
                name = macro_name,
                definition = definition,
                params = params,
                is_global = is_global,
                is_outer = is_outer,
                is_expanded = is_expanded,
                is_long = is_long,
                )

        macro_logger.info("  -- definition: %s", definition)
        macro_logger.debug("  -- object: %s", new_macro)

        tokens.state.set(
               field = macro_name,
               value = new_macro,
               use_global = is_global,
               block = 'controls',
               )

class Outer(Macro):

    """
    This handles all the modifiers which can precede \\def.
    All these modifiers are either this class or one of
    its subclasses.

    This class passes all the actual work on to Def.
    """

    def __call__(self, name, tokens):
        is_global = False
        is_outer = False
        is_long = False
        is_expanded = False

        token = name
        while True:
            if token is None or token.category != token.CONTROL:
                # XXX this message will be too confusing in
                # XXX many circumstances
                raise mex.exception.ParseError(
                        f"definitions must be followed by "+\
                                f"a control sequence (not {token})",
                                tokens)

            if token.name=='def':
                break
            elif token.name=='gdef':
                is_global = True
                break
            elif token.name=='edef':
                is_expanded = True
                break
            elif token.name=='xdef':
                is_expanded = True
                is_global = True
                break
            elif token.name=='global':
                is_global = True
            elif token.name=='outer':
                is_outer = True
            elif token.name=='long':
                is_long = True
            else:
                token = None
                continue

            token = tokens.__next__()
            macro_logger.info("read: %s", token)

        tokens.state.controls['def'](
                name = name, tokens = tokens,
                is_global = is_global,
                is_outer = is_outer,
                is_long = is_long,
                is_expanded = is_expanded,
                )

# These are all forms of definition,
# so they're handled as Def.

class Gdef(Outer): pass
class Global(Outer): pass # XXX "Global" can also precede simple defs
class Outer(Outer): pass
class Long(Outer): pass
class Edef(Outer): pass
class Xdef(Outer): pass

class Chardef_defined(Macro):
    pass

class Chardef(Macro):

    def __call__(self, name, tokens):

        tokens.running = False
        newname = tokens.__next__()
        tokens.running = True

        if newname.category != newname.CONTROL:
            raise mex.exception.ParseError(
                    f"{name} must be followed by a control, not {token}",
                    tokens)

        char = chr(mex.value.Number(tokens).value)

        # XXX do we really want to allow them to redefine
        # XXX *any* control?

        class Redefined_by_chardef(Chardef_defined):

            def __call__(self, name, tokens):
                tokens.push(char)

            def __repr__(self):
                return f"[{char}]"

            @property
            def value(self):
                return char

        tokens.state.set(
                field = newname.name,
                value = Redefined_by_chardef(),
                block = 'controls',
                )

class Mathchardef(Chardef):
    pass # TODO

class Par(Macro):
    def __call__(self, name, tokens):
        pass

class Message(Macro):
    def __call__(self, name, tokens):
        for t in Expander(
                tokens=tokens,
                single=True,
                running=False):
            if t.category in (t.LETTER, t.SPACE, t.OTHER):
                sys.stdout.write(t.ch)
            else:
                sys.stdout.write(str(t))

class Countdef(Macro):

    def __call__(self, name, tokens):

        tokens.running = False
        newname = tokens.__next__()
        tokens.running = True

        if newname.category != newname.CONTROL:
            raise mex.exception.ParseError(
                    f"{name} must be followed by a control, not {token}",
                    tokens)

        # XXX Optional equals
        # XXX Integer
        # XXX create a variable
        # XXX to here TODO

        char = chr(mex.value.Number(tokens).value)

        # XXX do we really want to allow them to redefine
        # XXX *any* control?

        class Redefined_by_chardef(Chardef_defined):

            def __call__(self, name, tokens):
                tokens.push(char)

            def __repr__(self):
                return f"[{char}]"

            @property
            def value(self):
                return char

        tokens.state.set(
                field = newname.name,
                value = Redefined_by_chardef(),
                block = 'controls',
                )

# TODO \let
# TODO \font

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

            macro_logger.debug("token: %s", token)

            if self.no_par:
                if token.category==token.CONTROL and token.name=='par':
                    raise mex.exception.ParseError(
                            "runaway expansion",
                            self.state)

            if self.single:
                if token.category==token.BEGINNING_GROUP:
                    self.single_grouping += 1

                    macro_logger.info("single_grouping now %d", self.single_grouping)
                    if self.single_grouping==1:
                        # don't pass the opening { through
                        continue
                elif self.single_grouping==0:
                    # First token wasn't a BEGINNING_GROUP,
                    # so we yield that and then stop.
                    macro_logger.debug("  -- the only symbol in a single")
                    yield token
                    return

                if token.category==token.END_GROUP:
                    self.single_grouping -= 1
                    if self.single_grouping==0:
                        macro_logger.debug("  -- the last } in a single")
                        return

            if not self.running:
                yield token
                continue

            if token is None:
                yield token

            elif token.category==token.BEGINNING_GROUP:
                self.state.begin_group()

            elif token.category==token.END_GROUP:
                try:
                    self.state.end_group()
                except ValueError as ve:
                    raise mex.exception.ParseError(
                            str(ve),
                            self)

            elif token.category==token.CONTROL:
                handler = self.state.get(token.name,
                        default=None,
                        tokens=self.tokens)

                if handler is None:
                    if len(token.name)==1:
                        # they used a control symbol which
                        # doesn't exist, so just give them
                        # the literal symbol they typed
                        self.push(
                                mex.token.Token(
                                    category = mex.token.Token.OTHER,
                                    ch = token.name,
                                    ))
                    else:
                        raise KeyError(f"there is no macro called {token.name}")
                elif self.no_outer and handler.is_outer:
                    raise mex.exception.ParseError(
                            "outer macro called where it shouldn't be",
                            self.state)
                else:
                    macro_logger.info('Calling macro: %s', handler)
                    # control exists, so run it.
                    handler_result = handler(
                            name = token,
                            tokens=self.tokens,
                            )
                    macro_logger.info('  -- with result: %s', handler_result)

                    if handler_result:
                        self.tokens.push(handler_result)
            else:
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

def handlers():

    # Take a copy. Sometimes evaluating a macro may
    # create another macro, which changes the size
    # of globals().items() and confuses the list comprehension.
    g = list(globals().items())

    result = dict([
            (name.lower(), value()) for
            (name, value) in g
            if value.__class__==type and
            value!=Macro and
            issubclass(value, Macro) and
            not name.startswith('_')
            ])

    return result
