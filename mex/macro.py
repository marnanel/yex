import logging
import mex.parse
import mex.value
import mex.exception
import mex.font
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
        raise mex.exception.MacroError(
                "superclass does nothing useful in itself",
                tokens)

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
            raise mex.exception.MacroError(
                    'not yet implemented',
                    tokens) # TODO

        interpolated = []
        for t in self.definition:
            if t.category==t.PARAMETER:
                for t2 in parameter_values[t.ch]:
                    interpolated.append(t2)
            else:
                interpolated.append(t)

        result = []
        for token in Expander(
                mex.parse.Tokeniser(
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
                        raise mex.exception.MacroError(
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
                is_outer = is_outer,
                is_expanded = is_expanded,
                is_long = is_long,
                )

        macro_logger.info("  -- definition: %s", definition)
        macro_logger.debug("  -- object: %s", new_macro)

        tokens.state.set(
               field = macro_name,
               value = new_macro,
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
        is_outer = False
        is_long = False
        is_expanded = False

        token = name

        def _raise_error():
            raise mex.exception.ParseError(
                    rf"\{self.name} must be followed by a "+\
                            f"definition (not {token})",
                            tokens)

        while True:
            if token.category != token.CONTROL:
                _raise_error()
            elif token.name=='def':
                break
            elif token.name=='gdef':
                tokens.state.next_assignment_is_global = True
                break
            elif token.name=='edef':
                is_expanded = True
                break
            elif token.name=='xdef':
                tokens.state.next_assignment_is_global = True
                is_expanded = True
                break
            elif token.name=='outer':
                is_outer = True
            elif token.name=='long':
                is_long = True
            else:
                _raise_error()

            token = tokens.__next__()
            macro_logger.info("read: %s", token)

        tokens.state.controls['def'](
                name = name, tokens = tokens,
                is_outer = is_outer,
                is_long = is_long,
                is_expanded = is_expanded,
                )

# These are all forms of definition,
# so they're handled as Def.

class Gdef(Outer): pass
class Outer(Outer): pass
class Long(Outer): pass
class Edef(Outer): pass
class Xdef(Outer): pass

class Global(Macro):
    def __call__(self, name, tokens):
        tokens.state.next_assignment_is_global = True

class _Defined(Macro):
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

        # XXX do we really want to allow them to redefine
        # XXX *any* control?

        tokens.eat_optional_equals()

        self.redefine_symbol(
                symbol = newname,
                tokens = tokens,
                )

    def redefine_symbol(self, symbol, tokens):

        char = chr(mex.value.Number(tokens).value)

        class Redefined_by_chardef(_Defined):

            def __call__(self, name, tokens):
                return char

            def __repr__(self):
                return "[chardef: %d]" % (ord(char),)

            @property
            def value(self):
                return char

        tokens.state.set(
                field = symbol.name,
                value = Redefined_by_chardef(),
                block = 'controls',
                )

class Mathchardef(Chardef):

    def redefine_symbol(self, symbol, tokens):
        mathchar = chr(mex.value.Number(tokens).value)

        # TODO there's nothing useful to do with this
        # until we implement math mode!

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

class _Registerdef(Macro):

    def __call__(self, name, tokens):

        tokens.running = False
        newname = tokens.__next__()
        tokens.running = True

        if newname.category != newname.CONTROL:
            raise mex.exception.ParseError(
                    f"{name} must be followed by a control, not {token}",
                    tokens)

        index = self.block + str(mex.value.Number(tokens).value)

        tokens.state.set(
                field = newname.name,
                value = tokens.state[index],
                block = 'controls',
                )

class Countdef(_Registerdef):
    block = 'count'

class Dimendef(_Registerdef):
    block = 'dimen'

class Skipdef(_Registerdef):
    block = 'skip'

class Muskipdef(_Registerdef):
    block = 'muskip'

class Toksdef(_Registerdef):
    block = 'toks'

# there is no Boxdef-- see the TeXbook, p121

class _Arithmetic(Macro):
    """
    Adds, multiplies, or divides two quantities.
    """
    def __call__(self, name, tokens):

        tokens.running = False
        lvalue_name = tokens.__next__()
        tokens.running = True

        lvalue = tokens.state.get(
                lvalue_name.name,
                default=None,
                tokens=tokens)

        tokens.optional_string("by")
        tokens.eat_optional_spaces()

        rvalue = lvalue.our_type(tokens)

        macro_logger.info(r"\%s %s by %s",
                name, lvalue, rvalue)

        self.do_operation(lvalue, rvalue)

class Advance(_Arithmetic):
    """
    Adds two quantities.
    """
    def do_operation(self, lvalue, rvalue):
        lvalue += rvalue

class Multiply(_Arithmetic):
    """
    Multiplies two quantities.
    """
    def do_operation(self, lvalue, rvalue):
        lvalue *= rvalue

class Divide(_Arithmetic):
    """
    Divides two quantities.
    """
    def do_operation(self, lvalue, rvalue):
        lvalue /= rvalue


class The(Macro):

    """
    Takes an argument, one of many kinds (see the TeXbook p212ff)
    and returns a representation of that argument.

    For example, \\the\\count100 returns a series of character
    tokens representing the contents of count100.
    """

    def __call__(self, name, tokens):
        tokens.running = False
        subject = tokens.__next__()
        tokens.running = True

        handler = tokens.state.get(subject.name,
                default=None,
                tokens=tokens)

        representation = handler.get_the()
        macro_logger.debug(r'\the for %s is %s',
                handler, representation)

        tokens.push(representation,
                clean_char_tokens=True)

class Let(Macro):
    """
    TODO
    """ # TODO

    def __call__(self, name, tokens):

        tokens.running = False
        lhs = tokens.__next__()
        tokens.running = True

        tokens.eat_optional_equals()

        tokens.running = False
        rhs = tokens.__next__()
        tokens.running = True

        if rhs.category==rhs.CONTROL:
            self.redefine_control(lhs, rhs, tokens)
        else:
            self.redefine_ordinary_token(lhs, rhs, tokens)

    def redefine_control(self, lhs, rhs, tokens):

        rhs_referent = tokens.state.get(rhs.name,
                        default=None,
                        tokens=tokens)

        if rhs_referent is None:
            raise mex.exception.MacroError(
                    rf"\let {lhs}={rhs}, but there is no such control",
                    tokens)

        macro_logger.info(r"\let %s = %s, which is %s",
                lhs, rhs, rhs_referent)

        tokens.state.set(
                field = lhs.name,
                value = rhs_referent,
                block = 'controls',
                )

    def redefine_ordinary_token(self, lhs, rhs, tokens):

        class Redefined_by_let(_Defined):

            def __call__(self, name, tokens):
                tokens.push(rhs)

            def __repr__(self):
                return f"[{rhs}]"

            @property
            def value(self):
                return rhs

        macro_logger.info(r"\let %s = %s",
                lhs, rhs)

        tokens.state.set(
                field = lhs.name,
                value = Redefined_by_let(),
                block = 'controls',
                )

class Font(Macro):
    """
    TODO
    """ # TODO

    def __call__(self, name, tokens):

        tokens.running = False
        fontname = tokens.__next__()
        tokens.running = True

        tokens.eat_optional_equals()

        filename = mex.filename.Filename(
                name = tokens,
                filetype = 'font',
                )
        filename.resolve()

        macro_logger.info(r"\font\%s=%s",
                fontname.name, filename.value)

        tokens.state.fonts[fontname.name] = mex.font.Metrics(
                filename = filename.path,
                )

        class Font_setter(Macro):
            def __call__(self, name, tokens):
                macro_logger.info("Setting font to %s",
                        filename.value)
                tokens.state['_currentfont'].value = filename.value

            def __repr__(self):
                return rf'[font = {filename.value}]'

        new_macro = Font_setter()

        tokens.state.set(
                field = fontname.name,
                value = new_macro,
                block = 'controls',
                )

        macro_logger.info("New font setter %s = %s",
                fontname.name,
                new_macro)

class Relax(Macro):
    """
    Does nothing.

    See the TeXbook, p275.
    """
    def __call__(self, name, tokens):
        pass

##############################

class _Hvbox(Macro):

    def __call__(self, name, tokens):
        for token in tokens:
            if token.category == token.BEGINNING_GROUP:
                # good
                break

            raise mex.exceptions.MexError(
                    f"{name} must be followed by a group",
                    tokens.state)

        tokens.state.begin_group()
        tokens.state['_mode'] = self.next_mode

class Hbox(_Hvbox):
    next_mode = 'restricted_horizontal'

class Vbox(_Hvbox):
    next_mode = 'internal_vertical'

##############################

class Noindent(Macro):
    def __call__(self, name, tokens):
        if tokens.state.mode.is_vertical:
            tokens.state['_mode'] = 'horizontal'
            self.maybe_add_indent(tokens.state.mode)

    def maybe_add_indent(self, mode):
        pass # no, not here

class Indent(Noindent):

    def maybe_add_indent(self, mode):
        pass # TODO

##############################

class _Conditional(Macro):
    """
    A command which affects the flow of control.
    """
    def __call__(self, name, tokens):
        """
        Executes this conditional. The actual work
        is delegated to self.do_conditional().
        """
        command_logger.debug(
                r"%s: from %s",
                name,
                tokens.state.ifdepth,
                )

        self.do_conditional(tokens)

    def do_conditional(self, tokens):
        """
        Decides whether the condition has been met, and
        what to do about it.
        """
        raise ValueError("superclass")

    def _do_true(self, state):
        """
        Convenience method for do_conditional() to call if
        the result is True.
        """
        state.ifdepth.append(
                state.ifdepth[-1])

    def _do_false(self, state):
        """
        Convenience method for do_conditional() to call if
        the result is False.
        """
        if state.ifdepth[-1]:
            command_logger.info("  -- was false; skipping")

        state.ifdepth.append(False)

class Iftrue(_Conditional):
    def do_conditional(self, tokens):
        self._do_true(tokens.state)

class Iffalse(_Conditional):
    def do_conditional(self, tokens):
        self._do_false(tokens.state)

class _Ifnum_or_Ifdim(_Conditional):
    def do_conditional(self, tokens):

        left = self._get_value(tokens)

        for op in tokens:
            if op.category!=12 or not op.ch in '<=>':
                raise mex.exception.ParseError(
                        "comparison operator must be <, =, or >"
                        f" (not {op})",
                        tokens.state)
            break

        right = self._get_value(tokens)

        if op.ch=='<':
            result = left.value<right.value
        elif op.ch=='=':
            result = left.value==right.value
        else:
            result = left.value>right.value

        command_logger.debug(
                r"\ifnum %s%s%s == %s",
                    left, op.ch, right, result)

        if result:
            self._do_true(tokens.state)
        else:
            self._do_false(tokens.state)

class Ifnum(_Ifnum_or_Ifdim):
    def _get_value(self, tokens):
        return mex.value.Number(tokens)

class Ifdim(_Ifnum_or_Ifdim):
    def _get_value(self, tokens):
        return mex.value.Dimen(tokens)

class Ifodd(_Conditional):
    def do_conditional(self, tokens):

        number = mex.value.Number(tokens)

        if int(number)%2==0:
            self._do_false(tokens.state)
        else:
            self._do_true(tokens.state)

class _Ifmode(_Conditional):
    def do_conditional(self, tokens):
        whether = self.mode_matches(tokens.state.mode)

        if whether:
            self._do_true(tokens.state)
        else:
            self._do_false(tokens.state)

class Ifvmode(_Ifmode):
    def mode_matches(self, mode):
        return mode.is_vertical

class Ifhmode(_Ifmode):
    def mode_matches(self, mode):
        return mode.is_horizontal

class Ifmmode(_Ifmode):
    def mode_matches(self, mode):
        return mode.is_math

class Ifinner(_Ifmode):
    def mode_matches(self, mode):
        return mode.is_inner

class Ifcat(_Conditional):
    def do_conditional(self, tokens):

        comparands = []
        e = Expander(tokens,
                no_outer=True,
                )

        for t in e:
            comparands.append(t)
            if len(comparands)>1:
                break

        command_logger.debug(
                r"\ifcat %s",
                comparands)

        if comparands[0].category==comparands[1].category:
            self._do_true(tokens.state)
        else:
            self._do_false(tokens.state)

class Fi(_Conditional):
    def do_conditional(self, tokens):

        state = tokens.state

        if len(state.ifdepth)<2:
            raise mex.exception.MexError(
                    r"can't \fi; we're not in a conditional block",
                    state)

        if state.ifdepth[:-2]==[True, False]:
            command_logger.info("  -- conditional block ended; resuming")

        state.ifdepth.pop()

class Else(_Conditional):

    def do_conditional(self, tokens):

        state = tokens.state

        if len(state.ifdepth)<2:
            raise MexError(r"can't \else; we're not in a conditional block",
                    state)

        if not state.ifdepth[-2]:
            # \else can't turn on execution unless we were already executing
            # before this conditional block
            return

        try:
            tokens.state.ifdepth[-1].else_case()
        except AttributeError:
            state.ifdepth.append(not state.ifdepth.pop())
            if state.ifdepth[-1]:
                command_logger.info(r"\else: resuming")
            else:
                command_logger.info(r"\else: skipping")

class Ifcase(_Conditional):

    class _Case:
        def __init__(self, number):
            self.number = number
            self.count = 0
            self.constant = None

        def __bool__(self):
            if self.constant is not None:
                return self.constant

            return self.number==self.count

        def next_case(self):
            command_logger.debug(r"\or: %s", self)

            if self.number==self.count:
                command_logger.info(r"\or: skipping")
                self.constant = False
                return

            self.count += 1

            if self.number==self.count:
                command_logger.info(r"\or: resuming")

        def else_case(self):
            if self.constant==False:
                return
            elif self.number==self.count:
                self.constant = False
                return

            command_logger.info(r"\else: resuming")
            self.constant = True

        def __repr__(self):
            if self.constant is not None:
                return f'({self.constant})'

            return f'{self.count}/{self.number}'

    def do_conditional(self, tokens):

        state = tokens.state

        number = mex.value.Number(tokens).value

        case = self._Case(
                number = number,
                )
        state.ifdepth.append(case)

        command_logger.debug(r"\ifcase: %s", case)

        if number!=0:
            command_logger.info(r"\ifcase on %d; skipping",
                    number)

class Or(_Conditional):
    def do_conditional(self, tokens):
        try:
            tokens.state.ifdepth[-1].next_case()
        except AttributeError:
            raise mex.exception.MexError(
                    r"can't \or; we're not in an \ifcase block",
                    state)

##############################

class Noexpand(Macro):
    def __call__(self, name, tokens):

        for t in tokens:
            return t

##############################

class Showlists(Macro):
    def __call__(self, name, tokens):
        tokens.state.showlists()

##############################

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

            elif token is None:
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
                                mex.parse.Token(
                                    category = mex.parse.Token.OTHER,
                                    ch = token.name,
                                    ))
                    else:
                        raise mex.exception.MacroError(
                                f"there is no macro called {token.name}",
                                self.tokens)

                elif isinstance(handler, _Conditional):
                    macro_logger.info('Calling conditional: %s', handler)
                    handler(name=token, tokens=self.tokens)

                elif self.no_outer and handler.is_outer:
                    raise mex.exception.MacroError(
                            "outer macro called where it shouldn't be",
                            self.tokens)

                elif self.state.ifdepth[-1]:
                    # We're not prevented from executing by \if.

                    command_logger.info("%s: %s",
                            self.state.mode, handler)
                    macro_logger.info('Calling macro: %s', handler)
                    # control exists, so run it.
                    handler_result = handler(
                            name = token,
                            tokens=self.tokens,
                            )
                    macro_logger.info('  -- with result: %s', handler_result)

                    if isinstance(handler, Noexpand):
                        command_logger.debug(
                                r"  -- yielding \noexpand token: %s",
                                handler_result)
                        yield handler_result
                    elif handler_result:
                        self.tokens.push(handler_result)
                else:
                    command_logger.info("Not executing %s because "+\
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
