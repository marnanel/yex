import logging
import mex.parse
import mex.value
import mex.exception
import mex.font
import sys

macro_logger = logging.getLogger('mex.macros')
command_logger = logging.getLogger('mex.commands')

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
                "superclass does nothing useful in itself")

    def __repr__(self):
        return f'[\\{self.name}]'

class C_UserDefined(Macro):

    def __init__(self,
            definition,
            parameter_text,
            *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.definition = definition
        self.parameter_text = parameter_text

    def __call__(self, name, tokens):

        macro_logger.debug('%s: delimiters=%s', name, self.parameter_text)
        arguments = self._part1_find_arguments(name, tokens)
        macro_logger.debug('%s: arguments=%s', name, arguments)
        interpolated = self._part2_interpolate(arguments)
        macro_logger.debug('%s: interpolated=%s', name, interpolated)
        result = self._part3_expand(tokens, interpolated)
        macro_logger.debug('%s: result=%s', name, result)

        return result

    def _part1_find_arguments(self, name, tokens):

        arguments = {}

        if not self.parameter_text:
            return arguments

        # Match the zeroth delimiter, i.e. the symbols
        # which must appear before any parameter.
        # This should be refactorable into the next part
        # later.
        e = mex.parse.Expander(tokens,
                no_outer=True,
                no_par=not self.is_long,
                )

        for tp, te in zip(
                self.parameter_text[0],
                e,
                ):

            macro_logger.debug("  -- arguments: %s %s", tp, te)
            if tp!=te:
                raise mex.exception.MacroError(
                        f"Use of {name} doesn't match its definition."
                        )

        # Now the actual parameters...
        for i, p in enumerate(self.parameter_text[1:]):

            macro_logger.debug("  -- params: %s %s", i, p)
            tokens.eat_optional_spaces()

            if p:
                # We're expecting some series of tokens
                # to delimit this argument.

                e = mex.parse.Expander(tokens,
                    no_outer=True,
                    no_par=not self.is_long,
                    running=False,
                    )

                seen = []
                depth = 0
                balanced = True
                arguments[i] = []

                for j, t in enumerate(e):

                    if j==0:
                        if t.category==t.BEGINNING_GROUP:
                            depth = 1
                        else:
                            balanced = False
                    else:
                        if t.category==t.BEGINNING_GROUP:
                            if depth==0:
                                balanced = False
                            depth += 1
                        elif t.category==t.END_GROUP:
                            depth -= 1
                            if depth==0:
                                seen = []

                    if depth==0 and p[len(seen)]==t:
                        seen.append(t)

                        if len(seen)==len(p):
                            # hurrah, done
                            if balanced:
                                arguments[i] = \
                                        arguments[i][1:-1]
                            break
                    elif seen:
                        e.push(t)
                        for s in reversed(seen[1:]):
                            e.push(s)
                        arguments[i].append(seen[0])
                        seen = []
                    else:
                        arguments[i].append(t)
            else:
                # Not delimited
                e = mex.parse.Expander(tokens,
                    no_outer=True,
                    no_par=not self.is_long,
                    running=False,
                    single=True,
                    )

                arguments[i] = list(e)

        # FIXME what if we run off the end?
        return arguments

    def _part2_interpolate(self, arguments):

        interpolated = []
        find_which_param = False

        for t in self.definition:

            if find_which_param:
                find_which_param = False

                if t.ch=='#':
                    interpolated.append(t)
                else:
                    # TODO catch param numbers that don't exist
                    interpolated.extend(
                            arguments[int(t.ch)-1],
                            )
            elif t.category==t.PARAMETER:
                find_which_param = True
            else:
                interpolated.append(t)

        if find_which_param:
            # self.definition has already been processed,
            # by us, so presumably this shouldn't come up
            raise mex.exception.ParseError(
                    "definition ended with a param sign "
                    "(shouldn't happen)"
                    )

        return interpolated

    def _part3_expand(self, tokens, interpolated):
        tokens.push(interpolated)
        result = []
        for token in mex.parse.Expander(
                tokens,
                no_outer = True,
                ):
            result.append(token)
        return result

    def __repr__(self):
        result = f'[\\{self.name}:'

        if self.parameter_text:
            result += '('
            for c in self.parameter_text:
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

        definition_extra = []
        token = tokens.__next__()
        macro_logger.debug("defining new macro:")
        macro_logger.debug("  -- macro name: %s", token)

        if token.category==token.CONTROL:
            macro_name = token.name
        elif token.category==token.ACTIVE:
            macro_name = token.ch
        else:
            raise mex.exception.ParseError(
                    f"definition names must be "+\
                            f"a control sequence or an active character" +\
                            f"(not {token})")

        parameter_text = [ [] ]
        param_count = 0

        for token in tokens:
            macro_logger.debug("  -- param token: %s", token)

            if token.category == token.BEGINNING_GROUP:
                tokens.push(token)
                break
            elif token.category == token.CONTROL:
                try:
                    if tokens.state.controls[token.name].is_outer:
                        raise mex.exception.MacroError(
                                "outer macros not allowed in param lists")
                except KeyError:
                    pass # Control doesn't exist, so can't be outer

                parameter_text[-1].append(token)
            elif token.category == token.PARAMETER:

                for which in tokens:
                    break

                if which.category==which.BEGINNING_GROUP:
                    # Special case. See "A special extension..." on
                    # p204 of the TeXbook.
                    parameter_text[-1].append(which)
                    definition_extra.append(which)

                elif int(which.ch) != param_count+1:
                    raise mex.exception.ParseError(
                            "parameters must occur in ascending order "
                            f"(found {which.ch}, needed {param_count+1})"
                            )
                else:
                    parameter_text.append( [] )
                    param_count += 1
            else:
                parameter_text[-1].append(token)

        macro_logger.debug("  -- parameter_text: %s", parameter_text)

        # now the definition
        definition = []

        for token in mex.parse.Expander(tokens,
                running=is_expanded,
                single=True,
                no_outer=True,
                ):
            macro_logger.debug("  -- definition token: %s", token)
            definition.append(token)

        definition.extend(definition_extra)

        new_macro = C_UserDefined(
                name = macro_name,
                definition = definition,
                parameter_text = parameter_text,
                is_outer = is_outer,
                is_expanded = is_expanded,
                is_long = is_long,
                )

        macro_logger.debug("  -- definition: %s", definition)
        macro_logger.debug("  -- object: %s", new_macro)

        tokens.state[macro_name] = new_macro

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
                            f"definition (not {token})")

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
            macro_logger.debug("read: %s", token)

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

class C_Defined(Macro):
    pass

class Chardef(Macro):

    def __call__(self, name, tokens):

        tokens.running = False
        newname = tokens.__next__()
        tokens.running = True

        if newname.category != newname.CONTROL:
            raise mex.exception.ParseError(
                    f"{name} must be followed by a control, not {token}")

        # XXX do we really want to allow them to redefine
        # XXX *any* control?

        tokens.eat_optional_equals()

        self.redefine_symbol(
                symbol = newname,
                tokens = tokens,
                )

    def redefine_symbol(self, symbol, tokens):

        char = chr(mex.value.Number(tokens).value)

        class Redefined_by_chardef(C_Defined):

            def __call__(self, name, tokens):
                return char

            def __repr__(self):
                return "[chardef: %d]" % (ord(char),)

            @property
            def value(self):
                return char

        tokens.state[symbol.name] = Redefined_by_chardef()

class Mathchardef(Chardef):

    def redefine_symbol(self, symbol, tokens):
        mathchar = chr(mex.value.Number(tokens).value)

        # TODO there's nothing useful to do with this
        # until we implement math mode!

class Par(Macro):
    def __call__(self, name, tokens):
        pass

#############

class C_StringMacro(Macro):
    def __call__(self, name, tokens,
            running=True):
        s = ''
        for t in mex.parse.Expander(
                tokens=tokens,
                single=True,
                running=False):
            if t.category in (t.LETTER, t.SPACE, t.OTHER):
                s += t.ch
            else:
                s += str(t)

        if running:
            self.handle_string(name, s)

class Message(C_StringMacro):
    def handle_string(self, name, s):
        sys.stdout.write(s)

class Errmessage(C_StringMacro):
    def handle_string(self, name, s):
        sys.stderr.write(s)

class Special(C_StringMacro):
    def handle_string(self, name, s):
        # does nothing by default
        pass

#############

class _Registerdef(Macro):

    def __call__(self, name, tokens):

        tokens.running = False
        newname = tokens.__next__()
        tokens.running = True

        if newname.category != newname.CONTROL:
            raise mex.exception.ParseError(
                    f"{name} must be followed by a control, not {newname}")

        index = self.block + str(mex.value.Number(tokens).value)
        existing = tokens.state.get(
                field = index,
                )
        command_logger.debug(r"%s sets \%s to %s",
                name,
                newname.name,
                existing)

        tokens.state[newname.name] = existing

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

        macro_logger.debug(r"\%s %s by %s",
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
                    rf"\let {lhs}={rhs}, but there is no such control")

        macro_logger.debug(r"\let %s = %s, which is %s",
                lhs, rhs, rhs_referent)

        tokens.state[lhs.name] = rhs_referent

    def redefine_ordinary_token(self, lhs, rhs, tokens):

        class Redefined_by_let(C_Defined):

            def __call__(self, name, tokens):
                tokens.push(rhs)

            def __repr__(self):
                return f"[{rhs}]"

            @property
            def value(self):
                return rhs

        macro_logger.debug(r"\let %s = %s",
                lhs, rhs)

        tokens.state[lhs.name] = Redefined_by_let()

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

        macro_logger.debug(r"\font\%s=%s",
                fontname.name, filename.value)

        tokens.state.fonts[fontname.name] = mex.font.Metrics(
                filename = filename.path,
                )

        class Font_setter(Macro):
            def __call__(self, name, tokens):
                macro_logger.debug("Setting font to %s",
                        filename.value)
                tokens.state['_currentfont'].value = filename.value

            def __repr__(self):
                return rf'[font = {filename.value}]'

        new_macro = Font_setter()

        tokens.state[fontname.name] = new_macro

        macro_logger.debug("New font setter %s = %s",
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

            raise mex.exception.MexError(
                    f"{name} must be followed by a group")

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

class C_Conditional(Macro):
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
            command_logger.debug("  -- was false; skipping")

        state.ifdepth.append(False)

class Iftrue(C_Conditional):
    def do_conditional(self, tokens):
        self._do_true(tokens.state)

class Iffalse(C_Conditional):
    def do_conditional(self, tokens):
        self._do_false(tokens.state)

class _Ifnum_or_Ifdim(C_Conditional):
    def do_conditional(self, tokens):

        left = self._get_value(tokens)
        macro_logger.debug("  -- left: %s", left)

        for op in tokens:
            if op.category!=12 or not op.ch in '<=>':
                raise mex.exception.ParseError(
                        "comparison operator must be <, =, or >"
                        f" (not {op})")
            break
        macro_logger.debug("  -- op: %s", op.ch)

        right = self._get_value(tokens)
        macro_logger.debug("  -- right: %s", right)

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

class Ifodd(C_Conditional):
    def do_conditional(self, tokens):

        number = mex.value.Number(tokens)

        if int(number)%2==0:
            self._do_false(tokens.state)
        else:
            self._do_true(tokens.state)

class _Ifmode(C_Conditional):
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

class _If_or_Ifcat(C_Conditional):
    def do_conditional(self, tokens):

        comparands = []
        e = mex.parse.Expander(tokens,
                no_outer=True,
                )

        for t in e:
            comparands.append(t)
            if len(comparands)>1:
                break

        command_logger.debug(
                r"\%s %s",
                self.__class__.__name__.lower(),
                comparands)

        if self.get_field(comparands[0])==\
                self.get_field(comparands[1]):
            self._do_true(tokens.state)
        else:
            self._do_false(tokens.state)

class If(_If_or_Ifcat):
    def get_field(self, t):
        return t.ch

class Ifcat(_If_or_Ifcat):
    def get_field(self, t):
        return t.category

class Fi(C_Conditional):
    def do_conditional(self, tokens):

        state = tokens.state

        if len(state.ifdepth)<2:
            raise mex.exception.MexError(
                    r"can't \fi; we're not in a conditional block")

        if state.ifdepth[:-2]==[True, False]:
            command_logger.debug("  -- conditional block ended; resuming")

        state.ifdepth.pop()

class Else(C_Conditional):

    def do_conditional(self, tokens):

        state = tokens.state

        if len(state.ifdepth)<2:
            raise MexError(r"can't \else; we're not in a conditional block")

        if not state.ifdepth[-2]:
            # \else can't turn on execution unless we were already executing
            # before this conditional block
            return

        try:
            tokens.state.ifdepth[-1].else_case()
        except AttributeError:
            state.ifdepth.append(not state.ifdepth.pop())
            if state.ifdepth[-1]:
                command_logger.debug(r"\else: resuming")
            else:
                command_logger.debug(r"\else: skipping")

class Ifcase(C_Conditional):

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
                command_logger.debug(r"\or: skipping")
                self.constant = False
                return

            self.count += 1

            if self.number==self.count:
                command_logger.debug(r"\or: resuming")

        def else_case(self):
            if self.constant==False:
                return
            elif self.number==self.count:
                self.constant = False
                return

            command_logger.debug(r"\else: resuming")
            self.constant = True

        def __repr__(self):
            if self.constant is not None:
                return f'({self.constant})'

            return f'{self.count}/{self.number}'

    def do_conditional(self, tokens):

        state = tokens.state

        number = int(mex.value.Number(tokens))

        case = self._Case(
                number = number,
                )
        state.ifdepth.append(case)

        command_logger.debug(r"\ifcase: %s", case)

        if number!=0:
            command_logger.debug(r"\ifcase on %d; skipping",
                    number)

class Or(C_Conditional):
    def do_conditional(self, tokens):
        try:
            tokens.state.ifdepth[-1].next_case()
        except AttributeError:
            raise mex.exception.MexError(
                    r"can't \or; we're not in an \ifcase block")

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
