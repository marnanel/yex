import string
import functools
import mex.exception

class Value():

    def __init__(self, tokens):
        self.tokens = tokens

    def optional_negative_signs(self):
        """
        Handles a sequence of +, -, and spaces.
        Returns whether the sign is negative.
        """
        is_negative = False
        c = None

        for c in self.tokens:

            if c.category==c.SPACE:
                continue
            elif c.category==c.OTHER:
                if c.ch=='+':
                    continue
                elif c.ch=='-':
                    is_negative = not is_negative
                    continue

            break

        if c is not None:
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
        """

        base = 10
        accepted_digits = string.digits

        try:
            c = self.tokens.__next__()
        except StopIteration:
            raise ValueError("reached eof with no number found")

        # XXX We need to deal with <coerced integer> too

        if c.category==c.OTHER:
            if c.ch=='`':
                # literal character, special case

                # "TeX does not expand this token, which should either
                # be a (character code, category code) pair,
                # or XXX an active character, or a control sequence
                # whose name consists of a single character.

                result = self.tokens.__next__()

                if result.category==result.CONTROL:
                    name = result.name
                    if len(name)!=1:
                        raise ValueError("Literal control sequences must "
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

            if result is None:
                raise mex.exception.MacroError(
                        f"there is no macro called {name}",
                        self.tokens)

            if isinstance(result, mex.macro._Defined):
                # chardef token used as internal integer;
                # see p267 of the TeXbook
                return ord(result.value)

            return result.value

        digits = ''
        for c in self.tokens:

            if c.category in (c.OTHER, c.LETTER):
                symbol = c.ch.lower()
                if symbol in accepted_digits:
                    digits += c.ch
                    continue

                elif symbol in '.,':
                    if can_be_decimal and base==10:
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
                # One optional space, at the end
                break
            else:
                # we don't know what this is, and it's
                # someone else's problem
                self.tokens.push(c)
                break

        if digits=='':
            raise ValueError(f"Expected a number but found {c}")

        if can_be_decimal:
            try:
                return float(digits)
            except ValueError:
                # Catches weird cases like "." as a number,
                # which is valid and means zero.
                return 0
        else:
            return int(digits, base)

    def optional_string(self, s):

        pushback = []

        for letter in s:
            c = self.tokens.__next__()
            pushback.append(c)

            if c.ch!=letter:
                for a in reversed(pushback):
                    self.tokens.push(a)
                return False

        return True

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

        if isinstance(v, int):
            super().__init__(None)
            self._value = v
            return

        super().__init__(v)

        is_negative = self.optional_negative_signs()

        self._value = self.unsigned_number()

        if is_negative:
            self._value = -self._value

    def __repr__(self):
        return f'{self.value}'

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

        if c1.category==c1.LETTER:
            if c1.ch in self.UNIT_FIRST_LETTERS:

                c2 = self.tokens.__next__()

                if c2.category==c2.LETTER:

                    unit = c1.ch+c2.ch

                    if unit in self.UNITS:
                        return unit

        raise ParseError("dimensions need a unit", self.tokens)

    def __init__(self, tokens):

        # See p266 of the TeXBook for the spec of a dimen.

        super().__init__(tokens)

        is_negative = self.optional_negative_signs()

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

        if is_negative:
            factor = -factor

        # units of measure that can be preceded by "true":
        #   pt | pc | in | bp | cm | mm | dd | cc | sp
        # internal units of measure that can't:
        #   em | ex
        #   and <internal integer>, <internal dimen>, and <internal glue>.

        is_true = self.optional_string(
                'true')

        unit = self._parse_unit_of_measurement()

        try:
            unit_size = self.UNITS[unit]
        except KeyError:
            raise mex.exception.ParseError(
                    f"dimensions need a unit, and I don't know {self.unit}",
                    tokens)

        if unit_size is None:
            current_font = self.tokens.state['_currentfont'].value

            if unit=='em':
                unit_size = current_font.quad
            elif unit=='ex':
                unit_size = current_font.xheight
            else:
                raise ValueError(f"unknown font-based unit {unit}")

        result = int(factor*unit_size)

        if not is_true:
            result *= self.tokens.state['mag'].value
            result /= 1000

        self.value = result

    def __str__(self):
        display_size = self.value / self.UNITS[self.DISPLAY_UNIT]
        return f'{display_size}{self.DISPLAY_UNIT}'
