import string
import functools
import mex.exception
import mex.parse
import logging

commands_logger = logging.getLogger('mex.commands')

class Value():

    def __init__(self, tokens):
        self.tokens = tokens

        try:
            if self.tokens.single:
                # This applies to Expanders, rather than Tokenisers.
                # If "single" is set, they exhaust after one symbol
                # or one group, which is a problem for us because
                # we don't know how many symbols we're going to have
                # to read in order to determine a Value, and also
                # because we need to push back the symbol after the
                # final one of the Value.
                raise mex.exception.MexError(
                        "Internal error: Values can't be constructed "
                        "from Expanders with single=True",
                        )
        except AttributeError:
            pass # probably a real Tokeniser

    def optional_negative_signs(self):
        """
        Handles a sequence of +, -, and spaces.
        Returns whether the sign is negative.
        """
        is_negative = False
        c = None

        for c in self.tokens:
            commands_logger.debug("  -- possible negative signs: %s", c)

            if c is None:
                break
            elif c.category==c.SPACE:
                continue
            elif c.category==c.OTHER:
                if c.ch=='+':
                    continue
                elif c.ch=='-':
                    is_negative = not is_negative
                    continue

            break

        if c is not None:
            commands_logger.debug(
                    "  -- possible negative signs: push back %s",
                    c)
            self.tokens.push(c)

        return is_negative

    def unsigned_number(self,
            can_be_decimal = False,
            ):
        """
        Reads in an unsigned number, as defined on
        p265 of the TeXbook. If "can_be_decimal" is True,
        we can also read in a decimal constant instead, as defined
        on page 266 of the TeXbook.

        If we find a control which is the name of a register,
        such as "\\dimen2", we return the value of that register.
        This means that the function might not return int or float
        (it might return Number or Dimen).
        """

        base = 10
        accepted_digits = string.digits

        for c in self.tokens:
            break
        else:
            raise mex.exception.MexError(
                    "Internal error: generator exhausted in Value")

        if c is None:
            raise mex.exception.ParseError(
                    "Unexpected end of file while looking for integer"
                    )
        elif c.category==c.OTHER:
            if c.ch=='`':
                # literal character, special case

                # "TeX does not expand this token, which should either
                # be a (character code, category code) pair,
                # or XXX an active character, or a control sequence
                # whose name consists of a single character.

                result = self.tokens.__next__()

                if result.category==result.CONTROL:
                    commands_logger.debug(
                            "reading value; backtick+control, %s",
                            result)

                    name = result.name
                    if len(name)!=1:
                        raise mex.exception.ParseError(
                                "Literal control sequences must "
                                f"have names of one character: {result}")
                    return ord(name[0])
                else:
                    return ord(result.ch)

            elif c.ch=='"':
                base = 16
                accepted_digits = string.hexdigits
            elif c.ch=="'":
                base = 8
                accepted_digits = string.octdigits
            elif c.ch in string.digits+'.,':
                self.tokens.push(c)

        elif c.category==c.CONTROL:

            name = c.name

            result = self.tokens.state.get(
                    name,
                    tokens=self.tokens,
                    )

            commands_logger.debug(
                    "  -- name==%s, ==%s",
                    name,
                    result)

            if result is None:
                raise mex.exception.MacroError(
                        f"there is no macro called {name}")

            if isinstance(result, mex.control.C_Defined):
                # chardef token used as internal integer;
                # see p267 of the TeXbook
                commands_logger.debug(
                        "  -- chardef, used as internal integer")
                return ord(result.value)

            return result

        commands_logger.debug(
                "  -- ready to read literal, accepted==%s",
                accepted_digits)

        digits = ''
        for c in self.tokens:
            commands_logger.debug(
                    "  -- found %s",
                    c)

            if c is None:
                break
            elif c.category in (c.OTHER, c.LETTER):
                symbol = c.ch.lower()
                if symbol in accepted_digits:
                    digits += c.ch
                    commands_logger.debug(
                            "  -- accepted; digits==%s",
                            digits)
                    continue

                elif symbol in '.,':
                    if can_be_decimal and base==10:
                        commands_logger.debug(
                                "  -- decimal point")
                        if '.' not in digits:
                            # XXX What does TeX do if there are
                            # multiple decimal points in the same
                            # number? The spec allows it.
                            digits += '.'
                        continue

                # it's an unknown symbol; stop
                self.tokens.push(c)
                break

            elif c.category==c.SPACE:
                commands_logger.debug(
                        "  -- final space; stop")

                # One optional space, at the end
                break
            else:
                commands_logger.debug(
                        "  -- don't know; stop")

                # we don't know what this is, and it's
                # someone else's problem
                self.tokens.push(c)
                break

        if digits=='':
            raise mex.exception.ParseError(
                    f"Expected a number but found {c}")

        commands_logger.debug(
                "  -- result is %s",
                digits)

        if can_be_decimal:
            try:
                return float(digits)
            except ValueError:
                # Catches weird cases like "." as a number,
                # which is valid and means zero.
                return 0
        else:
            return int(digits, base)

    def _check_same_type(self, other):
        """
        If other is exactly the same type as self, does nothing.
        Otherwise raises TypeError.

        Maybe this should work with subclasses too, idk. It
        doesn't actually make a difference for what we're doing.
        """
        if type(self)!=type(other):
            raise TypeError(
                    f"Can't add {self.__class__.__name__} "+\
                            f"to {other.__class__.__name__}.")

    def __iadd__(self, other):
        self._check_same_type(other)
        self.value += other.value
        return self

@functools.total_ordering
class Number(Value):

    def __init__(self, v):

        self._value = v
        if isinstance(v, int):
            super().__init__(None)
            return

        super().__init__(v)

        is_negative = self.optional_negative_signs()

        self._value = self.unsigned_number()

        if not isinstance(self._value, int):
            if is_negative:
                raise TypeError(
                        "unary negation only works on literals")
        try:
            self._value = int(self._value)
        except (TypeError, AttributeError):
            raise mex.exception.ParseError(
                    f"expected a Number, but found {self._value}")

        if is_negative:
            self._value = -self._value

    def __repr__(self):
        return f'{self._value}'

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, x):
        if not isinstance(x, int):
            raise TypeError("Numbers can only be integers")

        self._value = x

    # You can multiply and divide Numbers, but
    # not other kinds of Value.

    def __imul__(self, other):
        self._check_same_type(other)
        self._value *= other._value
        return self

    def __itruediv__(self, other):
        self._check_same_type(other)
        self._value /= other._value
        return self

    def __hash__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, int):
            return self.value==other
        elif isinstance(other, Number):
            return self.value==other.value
        else:
            raise TypeError(
                    f"Can't compare Number and {other.__class__.__name__}")

    def __lt__(self, other):
        if isinstance(other, int):
            return self.value<other
        elif isinstance(other, Number):
            return self.value<other.value
        else:
            raise TypeError(
                    f"Can't compare Number and {other.__class__.__name__}")

    def __int__(self):
        return self.value

@functools.total_ordering
class Dimen(Value):

    UNITS = {
            # per p57 of the TeXbook.
            # Units are in sp.
            # Scaling factors from texlive.
            "pt": 65536,             # Points
            "pc": 786432,            # Picas
            "in": 4736286,           # Inches
            "bp": 65782,             # Big points
            "cm": 1864680,           # Centimetres
            "mm": 186468,            # Millimetres
            "dd": 70124,             # Didot points
            "cc": 841489,            # Ciceros
            "sp": 1,                 # Scaled points

            # Units which depend on the current font.
            "em": None,
            "ex": None,

            # Units used for stretch/shrink in Glue,
            # and nowhere else
            "fi": None, # plus some number of "l"s
            }

    # I did have this set up so it calculated the value
    # on the fly, so it could change with the font. And
    # it remembered what unit you'd given it. But TeX
    # doesn't do this, and displays everything in pt,
    # so we do too.
    DISPLAY_UNIT = 'pt'

    UNIT_FIRST_LETTERS = set(
            [k[0] for k in UNITS.keys()])

    def _parse_unit_of_measurement(self):

        c1 = self.tokens.__next__()
        c2 = None

        if c1 is not None and c1.category==c1.LETTER:
            if c1.ch in self.unit_obj.UNIT_FIRST_LETTERS:

                c2 = self.tokens.__next__()

                if c2.category==c2.LETTER:

                    unit = c1.ch+c2.ch

                    if unit in self.unit_obj.UNITS:
                        return unit

        if c1 is not None:
            problem = c1.ch
            if c2 is not None:
                problem += c2.ch
        else:
            problem = 'end of file'

        raise mex.exception.ParseError(
                f"dimensions need a unit (found {problem})")

    def __init__(self, tokens=0,
            unit = None,
            infinity = 0,
            can_use_fil = False,
            unit_obj = None,
            ):

        self.unit_obj = unit_obj or self

        # See p266 of the TeXBook for the spec of a dimen.

        if isinstance(tokens, mex.parse.Tokeniser):
            super().__init__(tokens)

            self._parse_dimen(
                    tokens,
                    can_use_fil,
                    )
        else:
            super().__init__(None)
            self.value = float(tokens)
            self.infinity = infinity

            if unit is not None:
                try:
                    self.value *= self.unit_obj.UNITS[unit]
                except KeyError:
                    raise mex.exception.ParseError(
                            f"{self.unit_obj.__class__} "
                            f"does not know the unit {unit}")

    def _parse_dimen(self,
            tokens,
            can_use_fil,
            ):

        import mex.register
        import mex.parameter

        is_negative = self.optional_negative_signs()

        commands_logger.debug("reading Dimen; is_negative=%s",
                is_negative)

        # there follows one of:
        #   - internal dimen
        #   - factor + unit of measure
        #   - internal glue

        # "factor" is like a normal integer (as in Number)
        # except that it may contain dots or commas for
        # decimal points. If it does, it can't begin with
        # a base specifier, and it can't be an internal integer.
        factor = self.unsigned_number(
                can_be_decimal = True,
                )

        commands_logger.debug("reading Dimen; factor=%s",
                factor)

        # It's possible that "unsigned_number" has passed us the
        # value of a register it found (such as \dimen2), and
        # if so, we're done already.
        if isinstance(factor, (
            Dimen,
            mex.register.Register,
            mex.parameter.Parameter,
            )):

            if is_negative:
                raise mex.exception.ParseError(
                        "there is no unary negation of registers")

            if isinstance(factor, (
                mex.register.Register,
                mex.parameter.Parameter,
                )):
                factor = factor.value

            self.value = factor.value
            self.infinity = factor.infinity

            return

        if is_negative:
            factor = -factor

        # units of measure that can be preceded by "true":
        #   pt | pc | in | bp | cm | mm | dd | cc | sp
        # internal units of measure that can't:
        #   em | ex | fi(l+)
        #   and <internal integer>, <internal dimen>, and <internal glue>.

        is_true = self.tokens.optional_string(
                'true')
        self.infinity = 0

        unit = self._parse_unit_of_measurement()
        unit_size = self.unit_obj.UNITS[unit]

        if unit_size is None:

            if unit=='fi':
                if not can_use_fil:
                    raise mex.exception.ParseError(
                            "infinities are only allowed in plus/minus of Glue")

                for t in self.tokens:
                    if t.category==t.LETTER and t.ch=='l':
                        self.infinity += 1

                        if self.infinity==3:
                            break
                    else:
                        self.tokens.push(t)
                        break

                if self.infinity==0:
                    # "fi", with no "l"s
                    raise mex.exception.ParseError(
                            f"unknown unit fi")

                unit_size = 1 # nominally

            else:
                current_font = self.tokens.state['_currentfont'].value

                if unit=='em':
                    unit_size = current_font.quad
                elif unit=='ex':
                    unit_size = current_font.xheight
                else:
                    raise mex.exception.ParseError(
                            f"unknown unit {unit}")

        result = int(factor*unit_size)

        if not is_true:
            result *= int(self.tokens.state['mag'])
            result /= 1000

        self.value = result

    def __repr__(self):
        if self.infinity==0:
            unit = self.unit_obj.DISPLAY_UNIT
            display_size = self.value / self.unit_obj.UNITS[unit]
        else:
            unit = 'fi'+'l'*int(self.infinity)
            display_size = int(self.value)
        return '%.5g%s' % (display_size, unit)

    def __float__(self):
        return self.value

    def __eq__(self, other):
        return self.value==other.value

    def __lt__(self, other):
        return self.value<other.value

    def __int__(self):
        return int(self.value) # in sp

class Glue(Value):
    """
    A space between the smaller Boxes inside a Box.

    A Glue has space, stretch, and shrink.

    The specifications for Glue may be found in ch12
    of the TeXbook, beginning on page 69.
    """

    def __init__(self,
            t = None,
            unit = None,
            space = 0.0,
            stretch = 0.0,
            shrink = 0.0,
            stretch_infinity = 0,
            shrink_infinity = 0,
            ):

        """
        t can be a Tokeniser,
            in which case we attempt to parse a Glue from it.
        Or it can be numeric,
            in which case it overrides "space".
        Or it can be None.

        space, stretch, and shrink are all numeric. They're passed to
        Dimen()'s constructor along with the unit supplied.

        stretch_infinity and shrink_infinity are integers
        which will be supplied to Dimen's constructor along
        with stretch and shrink.
        """

        self.length = Dimen()

        if t is not None:
            if isinstance(t, mex.parse.Tokeniser):
                self.tokens = t
                self._parse_glue()
                return
            else:
                space = t

        self.tokens = None
        self.space = Dimen(space,
                unit=unit)
        self.stretch = Dimen(stretch,
                infinity = stretch_infinity,
                unit=unit)
        self.shrink = Dimen(shrink,
                infinity = shrink_infinity,
                unit=unit)
        self.length.value = self.space.value

    def _raise_parse_error(self):
        """
        I'm sorry, I haven't a Glue
        """
        raise mex.exception.MexError(
                "Expected a Glue")

    def _parse_glue(self):

        import mex.register
        import mex.parameter

        # We're either looking for
        #    optional_negative_signs and then one of
        #       * glue parameter
        #       * \lastskip
        #       * a token defined with \skipdef
        #       * \skipNNN register
        # Or
        #    Dimen,
        #       optionally followed by "plus <dimen>",
        #       optionally followed by "minus <dimen>"
        #    and in the plus/minus section, the units
        #     "fil+", i.e. "fi" plus any number of "l"s,
        #     are also allowed.

        for handler in [
            self._parse_glue_variable,
            self._parse_glue_literal,
            ]:

            if handler(self.tokens):
                return

        self._raise_parse_error()

    def _parse_glue_variable(self, tokens):
        """
        Attempts to initialise this object from
        a variable containing a Glue.

        Returns True if it succeeds. Otherwise, backs up to where
        it started and returns False.
        """

        is_negative = self.optional_negative_signs()

        commands_logger.debug("reading Glue; is_negative=%s",
                is_negative)

        for t in self.tokens:
            break

        if not t.category==t.CONTROL:
            # this is not a Glue variable; rewind
            self.tokens.push(t)
            # XXX If there were +/- symbols, this can't be a
            # valid Glue, so call self._raise_parse_error()

            commands_logger.debug("reading Glue; not a variable")
            return False

        control = self.tokens.state.get(
                field = t.name,
                tokens = self.tokens,
                )

        value = control.value

        if not isinstance(value, Glue):
            commands_logger.debug(
                    "reading Glue; %s==%s, which is not a control but a %s",
                    control, value, type(value))
            self._raise_parse_error()

        self.space = value.space
        self.stretch = value.stretch
        self.shrink = value.shrink

        self.length.value = self.space.value

        return True

    def _parse_glue_literal(self, tokens):
        """
        Attempts to initialise this object from
        a literal representing a Glue.

        Returns True if it succeeds. Otherwise, returns False.
        (Doesn't back up to where it started; if we return
        False it's always a fatal error.)

        Note: At present we always return True. If this isn't a
        real Glue literal it'll fail on attempting to read
        the first Dimen.
        """

        unit_obj = self._dimen_units()

        self.space = Dimen(tokens,
                    unit_obj=unit_obj,
                    )
        self.length.value = self.space.value

        tokens.eat_optional_spaces()

        if tokens.optional_string("plus"):
            self.stretch = Dimen(tokens,
                    can_use_fil=True,
                    unit_obj=unit_obj,
                    )
            tokens.eat_optional_spaces()
        else:
            self.stretch = Dimen(0)

        if tokens.optional_string("minus"):
            self.shrink = Dimen(tokens,
                    can_use_fil=True,
                    unit_obj=unit_obj,
                    )
            tokens.eat_optional_spaces()
        else:
            self.shrink = Dimen(0)

        return True

    def __repr__(self):
        result = f"{self.space}"

        if self.shrink.value:
            result += f" plus {self.stretch} minus {self.shrink}"
        elif self.stretch.value:
            result += f" plus {self.stretch}"

        return result

    def _dimen_units(self):
        return None # use the default units for Dimens

    def __eq__(self, other):
        return self.space==other.space and \
                self.stretch==other.stretch and \
                self.shrink==other.shrink

    def __int__(self):
        return int(self.space) # in sp

class Muglue(Glue):
    UNITS = {
            "mu": 1,
            "fi": None,
            }

    DISPLAY_UNIT = 'mu'

    UNIT_FIRST_LETTERS = set(['m', 'f'])

    def _dimen_units(self):
        return self

class Tokenlist(Value):
    def __init__(self,
            tokens = None):

        super().__init__(tokens)

        if tokens is None:
            self.value = []
        elif isinstance(tokens, list):
            self.tokens = None
            self.value = []
        else:
            raise NotImplementedError() # TODO

    def __eq__(self, other):
        return self.value==other.value
