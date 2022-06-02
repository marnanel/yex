import string
import functools
import yex.exception
import yex.parse
import logging
from yex.value.value import Value

logger = logging.getLogger('yex.general')

SP_TO_PT = 1/65536.0

@functools.total_ordering
class Dimen(Value):
    """
    A length.

    Attributes:
        value (int): The number of "scaled points", which are 1/65536 of
            an ordinary point. The external world sees and sets the value
            in a float of ordinary points; this is just kept as an integer
            for precision's sake.

            See also "infinity", for an exception to these rules.

        infinity (int): If this is zero, which it usually is, the "value"
            attribute is a number of "scaled points". If and only if
            the Dimen is the value of the "stretch" or "shrink" attribute of
            a Glue or Muglue, this attribute can also be 1, 2, or 3.
            In those cases, the Dimen is infinitely long

            Infinite Dimens are always longer than finite Dimens.
            An infinite Dimen is longer than another infinite Dimen
            if its "infinity" attribute is greater; if they're the
            same, we compare the "value" attribute.

            Infinite Dimens have a unit of "fil", "fill", or "filll",
            where the number of "l"s is the value of the "infinity" attribute.

            I apologise for the complexity here; it was Knuth's idea,
            not mine.

        UNITS (dict, class attribute): maps unit names to integer numbers of
            "scaled points", each of which is 1/65536 of a regular point.
            However, if the value is None, the calculation will be
            special-cased: "em" and "ex" are calculated with respect to
            the current font, and "fil", "fill", and "filll" are as
            explained in the documentation for the "infinity" attribute.

        unit_obj: usually equal to self. Unit size is always looked up
            in self.unit_obj.UNITS. This allows you to change the
            kind of units a Dimen uses, which is occasionally useful.
    """

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

    def _parse_unit_of_measurement(self, tokens):
        """
        Reads the next one or two tokens.

        If they're the name of a unit, as listed in self.unit_obj.UNITS,
        we return that name as a string.

        If the first token is any kind of control, we return that control
        without consuming anything after it.

        Otherwise, we raise an error.
        """

        c1 = tokens.next()
        c2 = None

        if isinstance(c1, yex.parse.Letter):
            if c1.ch in self.unit_obj.UNIT_FIRST_LETTERS:

                c2 = tokens.next()

                if isinstance(c2, yex.parse.Letter):

                    unit = c1.ch+c2.ch

                    if unit in self.unit_obj.UNITS:
                        logger.debug("reading Dimen: unit is %s",
                                unit)
                        return unit

        if c1 is not None:

            logger.debug("reading Dimen: that wasn't a unit")

            if isinstance(c1, yex.parse.Control):
                return c1

            problem = c1.ch
            if c2 is not None:
                problem += c2.ch
        else:
            problem = 'end of file'

        raise yex.exception.ParseError(
                f"dimensions need a unit (found {problem})")

    def __init__(self, t=0,
            unit = None,
            can_use_fil = False,
            unit_obj = None,
            ):

        super().__init__()
        self.unit_obj = unit_obj or self

        if isinstance(t, Dimen):
            self.value = int(t.value)
            self.infinity = t.infinity
            self.unit_obj = t.unit_obj

        elif isinstance(t, yex.parse.Tokenstream):

            # See p266 of the TeXBook for the spec of a dimen.
            self._parse_dimen(
                    self.prep_tokeniser(t),
                    can_use_fil,
                    )

        else:
            self.value = float(t)
            self.infinity = 0

            def _unit_not_known(name):
                raise yex.exception.ParseError(
                        f"{self.unit_obj.__class__} "
                        f"does not know the unit {unit}")

            if unit is None:
                unit = self.unit_obj.DISPLAY_UNIT

            if isinstance(unit, int):
                self.value *= unit
            elif can_use_fil and unit in ('fil', 'fill', 'filll'):
                    self.infinity = len(unit)-2
            else:
                try:
                    factor = self.unit_obj.UNITS[unit]
                except KeyError:
                    _unit_not_known(unit)

                self.value *= factor

            self.value = int(self.value)

    @classmethod
    def from_another(cls, another,
            value = None):

        result = cls.__new__(cls)

        if value is None:
            result.value = another.value
        else:
            result.value = int(value)

        result.infinity = another.infinity
        result.unit_obj = another.unit_obj

        return result

    def _parse_dimen(self,
            tokens,
            can_use_fil,
            ):

        import yex.register
        import yex.control

        is_negative = self.optional_negative_signs(tokens)

        logger.debug("reading Dimen; is_negative=%s",
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
                tokens,
                can_be_decimal = True,
                )

        logger.debug("reading Dimen; factor=%s (%s)",
                factor, type(factor))

        # It's possible that "unsigned_number" has passed us the
        # value of a register it found (such as \dimen2), and
        # if so, we're done already.
        if isinstance(factor, (
            Dimen,
            yex.register.Register,
            yex.control.C_Parameter,
            )):

            if is_negative:
                raise yex.exception.ParseError(
                        "there is no unary negation of registers")

            if isinstance(factor, (
                yex.register.Register,
                yex.control.C_Parameter,
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

        is_true = tokens.optional_string(
                'true')
        self.infinity = 0

        unit = self._parse_unit_of_measurement(tokens)
        if isinstance(unit, str):
            unit_size = self.unit_obj.UNITS[unit]
        else:
            tokens.push(unit)
            n = yex.value.Dimen(tokens)
            unit_size = n.value

            logger.debug(
                    "unit size was a reference: %g*%g (%dsp)",
                    factor, n, unit_size)

        if unit_size is None:

            if unit=='fi':
                if not can_use_fil:
                    raise yex.exception.ParseError(
                            "infinities are only allowed in plus/minus of Glue")

                for t in tokens:
                    if isinstance(t, yex.parse.Letter) and t.ch=='l':
                        self.infinity += 1

                        if self.infinity==3:
                            break
                    else:
                        tokens.push(t)
                        break

                if self.infinity==0:
                    # "fi", with no "l"s
                    raise yex.exception.ParseError(
                            f"unknown unit fi")

                unit_size = 1 # nominally

            else:
                current_font = tokens.doc['_font']

                if unit=='em':
                    unit_size = current_font.metrics.dimens[6].value # quad width
                elif unit=='ex':
                    unit_size = current_font.metrics.dimens[5].value # x-height
                else:
                    raise yex.exception.ParseError(
                            f"unknown unit {unit}")

        result = int(factor*unit_size)

        if not is_true:
            result *= int(tokens.doc[r'\mag'])
            result /= 1000

        self.value = result

    def __repr__(self,
            show_unit=True):
        """
        Args:
            show_unit (bool): whether to show the unit. This has no effect
                if the dimen is infinite: infinity units ("fil" etc)
                will always be displayed.
        """

        if self.infinity==0:
            unit = self.unit_obj.DISPLAY_UNIT
            display_size = self.value / self.unit_obj.UNITS[unit]
        else:
            unit = 'fi'+'l'*int(self.infinity)
            display_size = int(self.value)

        if show_unit or self.infinity!=0:
            return '%.5g%s' % (display_size, unit)
        else:
            return '%.5g' % (display_size)

    def __float__(self):
        if self.infinity!=0:
            return float(self.value)
        return self.value / self.unit_obj.UNITS[self.unit_obj.DISPLAY_UNIT]

    def __eq__(self, other):
        if not isinstance(other, Dimen):
            try:
                return float(self)==float(other)
            except TypeError:
                return False
        elif type(self.unit_obj)!=type(other.unit_obj):
            return False
        elif self.infinity!=other.infinity:
            return False
        else:
            return self.value==other.value

    def __lt__(self, other):
        if not isinstance(other, Dimen):
            return float(self) < float(other)
        elif type(self.unit_obj)!=type(other.unit_obj):
            raise yex.exception.YexError(
                    "Can't compare different kinds of dimen")
        elif self.infinity!=other.infinity:
            return self.infinity<other.infinity
        else:
            return self.value<other.value

    def __round__(self):
        """
        Returns a new Dimen whose value is the same as ours, but rounded.

        Rounding is with respect to the display unit, which is usually
        points. So a Dimen of 7.5pt will round to 7pt.
        """

        value = round(float(self))
        value *= self.unit_obj.UNITS[self.unit_obj.DISPLAY_UNIT]

        return self.from_another(self, value=value)

    def __int__(self):
        """
        Returns the length in points (or whatever the display unit is).

        If you want it in scaled points, access the "value" attribute
        directly.
        """
        return int(float(self))

    def _check_comparable(self, other):
        """
        Checks that the Dimen `other` is comparable with us:
        the units are the same kind (mm is the same kind as sp,
        for example, but mu is not) and that the infinity levels
        are the same.
        """
        if type(other.unit_obj)!=type(self.unit_obj):
            raise yex.exception.YexError(
                    f"{self} and {other} are measuring different "
                    "kinds of things")
        elif other.infinity!=self.infinity:
            raise yex.exception.YexError(
                    f"{self} and {other} are infinitely different")

    def _display_unit_to_sp(self, v):
        """
        Converts a number in the display unit (often pt) to scaled points.

        Scaled points are the unit that self.value is in.
        This is the reverse operation to `float()`.

        Args:
            v (float): a number in the display unit

        Returns:
            the number of scaled points. Always an integer.
        """

        unit = self.unit_obj.DISPLAY_UNIT
        return int(v*self.unit_obj.UNITS[unit])

    def __iadd__(self, other):
        if isinstance(other, (int, float)):
            self.value += self._display_unit_to_sp(other)
        elif isinstance(other, Dimen):
            self._check_same_type(other,
                    "Can't add %(them)s to %(us)s.")
            self.value += other.value

        return self

    def __isub__(self, other):
        if isinstance(other, (int, float)):
            self.value -= self._display_unit_to_sp(other)
        elif isinstance(other, Dimen):
            self._check_same_type(other,
                    "Can't subtract %(them)s from %(us)s.")
            self.value -= other.value

        return self

    def __imul__(self, other):
        self._check_numeric_type(other,
                "You can only multiply %(us)s by numeric values, "
                "not %(them)s.")
        self.value = int(self.value * float(other))
        return self

    def __itruediv__(self, other):
        self._check_numeric_type(other,
                "You can only divide %(us)s by numeric values, "
                "not %(them)s.")
        self.value = int(self.value / float(other))
        return self

    def __add__(self, other):
        if other==0:
            # Zero is the only numeric value you can add to a Dimen.
            # This makes sum() work neatly.
            return self
        self._check_same_type(other,
                "Can't add %(them)s to %(us)s.")
        self._check_comparable(other)
        result = self.from_another(self, value=self.value + other.value)
        return result

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        self._check_same_type(other,
                "Can't subtract %(them)s from %(us)s.")
        result = self.from_another(self, value=self.value - other.value)
        return result

    def __mul__(self, other):
        self._check_numeric_type(other,
                "You can only multiply %(us)s by numeric values, "
                "not %(them)s.")
        result = self.from_another(self, value=self.value * float(other))
        return result

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        self._check_numeric_type(other,
                "You can only divide %(us)s by numeric values, "
                "not %(them)s.")
        return self.from_another(self, value=self.value / float(other))

    def __neg__(self):
        return self.from_another(self, value=-self.value)

    def __pos__(self):
        return self.from_another(self, value=self.value)

    def __abs__(self):
        return self.from_another(self, value=abs(self.value))
