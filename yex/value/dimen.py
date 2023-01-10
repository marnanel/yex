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

        unit_cls: usually equal to this same class. Unit size is always
            looked up in self.unit_cls.UNITS. This allows you to change the
            kind of units a Dimen uses, which is occasionally useful.
            If you do use a different unit_cls, it must contain
            DISPLAY_UNIT and UNIT_FIRST_LETTERS attributes as well as UNITS.
            UNITS[DISPLAY_UNIT] should always equal 65536.
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

            # Our own:
            "px": (72*65536)/96,     # Pixels-- exactly 49152

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

    def __init__(self, length=0,
            unit = None,
            can_use_fil = False,
            unit_cls = None,
            ):

        super().__init__()
        self.unit_cls = unit_cls or self.__class__
        unit = unit or self.unit_cls.DISPLAY_UNIT

        self.value = float(length)
        self.infinity = 0

        if isinstance(unit, int):
            self.value *= unit
        elif unit in ('fil', 'fill', 'filll'):
            if can_use_fil:
                self.infinity = len(unit)-2
            else:
                raise yex.exception.ForbiddenInfinityError()

            self.value *= 65536
        else:
            try:
                factor = self.unit_cls.UNITS[unit]
            except KeyError:
                raise yex.exception.UnknownUnitError(
                        unit_class = self.unit_cls.__name__,
                        unit = unit,
                        )

            if factor is None:
                raise yex.exception.YexError(
                        f'unit "{unit}" is too complex for a literal; '
                        "if you don't like this, please fix it"
                        )

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
        result.unit_cls = another.unit_cls

        return result

    @classmethod
    def from_tokens(cls,
            tokens,
            can_use_fil=False,
            unit_cls=None,
            ):
        """
        Factory method: parses a Dimen from a token stream.

        See p266 of the TeXBook for the spec of a dimen.

        Args:
            tokens: the token stream
            can_use_fil: if True, the units "fil", "fill", and "filll"
                may be used, to represent the three possible kinds of
                infinity. If False (the default), they may not.
            unit_cls (class or None): the class to take the units from.
                This allows other classes to substitute their own units.

        Returns:
            A new Dimen, constructed according to the tokens found.
        """

        import yex.control

        tokens = cls.prep_tokeniser(tokens)
        unit_cls = unit_cls or cls

        # there follows one of:
        #   - internal dimen
        #   - factor + unit of measure
        #   - internal glue

        # "factor" is like a normal integer (as in Number)
        # except that it may contain dots or commas for
        # decimal points. If it does, it can't begin with
        # a base specifier, and it can't be an internal integer.
        factor = cls.get_value_from_tokens(
                tokens,
                can_be_decimal = True,
                )

        logger.debug("reading Dimen; factor=%s (%s)",
                factor, type(factor))

        def _dimen_reference_to_dimen(ref):
            if isinstance(ref, (
                yex.control.C_Register,
                yex.control.C_Parameter,
                )):
                ref = ref.value

            result = Dimen.from_another(ref)
            return result

        # It's possible that "unsigned_number" has passed us the
        # value of a register it found (such as \dimen2), and
        # if so, we're done already.
        if isinstance(factor, (
            Dimen,
            yex.control.C_Register,
            yex.control.C_Parameter,
            )):

            return _dimen_reference_to_dimen(factor)

        # units of measure that can be preceded by "true":
        #   pt | pc | in | bp | cm | mm | dd | cc | sp
        # internal units of measure that can't:
        #   em | ex | fi(l+)
        #   and <internal integer>, <internal dimen>, and <internal glue>.

        is_true = tokens.optional_string(
                'true')
        infinity = 0

        unit = cls._parse_unit_of_measurement(tokens,
                unit_cls = unit_cls,
                )

        if isinstance(unit, str):
            unit_size = unit_cls.UNITS[unit]
        else:
            n = _dimen_reference_to_dimen(unit)
            unit_size = n.value

            logger.debug(
                    "unit size was a reference: %g*%g (%dsp)",
                    factor, n, unit_size)

        if unit_size is None:

            if unit=='fi':
                if not can_use_fil:
                    raise yex.exception.ForbiddenInfinityError()

                for t in tokens:
                    if isinstance(t, yex.parse.Letter) and t.ch=='l':
                        infinity += 1

                        if infinity==3:
                            break
                    else:
                        tokens.push(t)
                        break

                if infinity==0:
                    # "fi", with no "l"s
                    raise yex.exception.UnknownUnitError(
                            unit_class = self.unit_cls.__name__,
                            unit = 'fi',
                            )

                unit_size = 65536 # nominally

            else:
                current_font = tokens.doc['_font']

                if unit=='em':
                    # quad width
                    unit_size = current_font.em.value
                elif unit=='ex':
                    # x-height
                    unit_size = current_font.ex.value
                else:
                    raise yex.exception.UnknownUnitError(
                            unit_class = self.unit_cls.__name__,
                            unit = unit,
                            )

        length = round(factor*65536)*unit_size
        length = round(length/65536)
        logger.debug("reading Dimen: %s*%s == %s",
                factor, unit_size, length)

        if not is_true:
            length *= int(tokens.doc[r'\mag'])
            length /= 1000
            logger.debug('reading Dimen: adjusted for non-"true": %s',
                    length)

        result = Dimen(
                length = length,
                unit = 1,
                unit_cls = unit_cls,
                )
        result.infinity = infinity

        logger.debug("reading Dimen: result is %s", result)

        return result

    @classmethod
    def _parse_unit_of_measurement(cls, tokens, unit_cls):
        """
        Reads the next one or two tokens.

        If they're the name of a unit, as listed in unit_cls.UNITS,
        we return that name as a string.

        If the first token is any kind of control, we return that control
        without consuming anything after it.

        Otherwise, we raise an error.
        """

        c1 = tokens.next(level='expanding')
        c2 = None

        if isinstance(c1, (yex.parse.Letter, yex.parse.Other)):
            if c1.ch in unit_cls.UNIT_FIRST_LETTERS:

                c2 = tokens.next()

                if isinstance(c2, (yex.parse.Letter, yex.parse.Other)):

                    unit = c1.ch+c2.ch

                    if unit in unit_cls.UNITS:
                        logger.debug("reading Dimen: unit is %s",
                                unit)
                        return unit

        if c1 is not None:

            if isinstance(c1, (
                yex.parse.Control,
                yex.control.C_Control,
                )):
                return c1

            problem = c1.ch
            if c2 is not None:
                problem += c2.ch
                logger.debug((
                    "reading Dimen: expected a unit but found %s and %s "
                    "(which are %s and %s)"),
                    c1, c2,
                    c1.__class__.__name__,
                    c2.__class__.__name__,
                    )

            else:
                logger.debug((
                    "reading Dimen: expected a unit but found %s "
                    "(which is a %s)"),
                    c1,
                    c1.__class__.__name__,
                    )

        else:
            problem = 'EOF'
            logger.debug("reading Dimen: expected a unit but found eof")

        raise yex.exception.NoUnitError(
                problem = problem,
                )

    def __repr__(self,
            show_unit=True):
        """
        Args:
            show_unit (bool): whether to show the unit. This has no effect
                if the dimen is infinite: infinity units ("fil" etc)
                will always be displayed.
        """

        try:
            result = yex.util.fraction_to_str(self.value, 16)

            if self.infinity!=0:
                result += 'fi'+'l'*self.infinity
            elif show_unit:
                result += self.unit_cls.DISPLAY_UNIT

            return result

        except AttributeError as e:
            return f'[{self.__class__.__name__}; inchoate]'

    def __float__(self):
        if self.infinity!=0:
            return self.value/65536
        return self.value / self.unit_cls.UNITS[self.unit_cls.DISPLAY_UNIT]

    def __eq__(self, other):
        if not isinstance(other, Dimen):
            try:
                diff = float(self)-float(other)
            except (TypeError, ValueError):
                return False

            return diff==0

        elif type(self.unit_cls)!=type(other.unit_cls):
            return False
        elif self.infinity!=other.infinity:
            return False
        else:
            diff = self.value-other.value
            if diff!=0 and abs(diff)<145:
                # 145sp is the longest wavelength of visible light
                logger.debug("beware: comparison between two near-as-dammit "
                        f"Dimens: {self.value} vs {other.value}, "
                        f"  both ≈ {self}")

            return diff==0

    def __lt__(self, other):
        if not isinstance(other, Dimen):
            return float(self) < float(other)
        elif type(self.unit_cls)!=type(other.unit_cls):
            raise yex.exception.DifferentUnitClassError(
                    us = self,
                    them = other,
                    )
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
        value *= self.unit_cls.UNITS[self.unit_cls.DISPLAY_UNIT]

        return self.from_another(self, value=value)

    def __int__(self):
        """
        Returns the length in points (or whatever the display unit is).

        If you want it in scaled points, access the "value" attribute
        directly.
        """
        return int(float(self))

    def __bool__(self):
        """
        Returns False if our value is zero, and True otherwise.
        """
        return self.value != 0

    def _check_comparable(self, other):
        """
        Checks that the Dimen `other` is comparable with us:
        the units are the same kind (mm is the same kind as sp,
        for example, but mu is not) and that the infinity levels
        are the same.
        """
        if type(other.unit_cls)!=type(self.unit_cls):
            raise yex.exception.DifferentUnitClassError(
                    us = self,
                    them = other,
                    )
        elif other.infinity!=self.infinity:
            raise yex.exception.DifferentInfinityError(
                    us = self,
                    them = other,
                    )

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

        unit = self.unit_cls.DISPLAY_UNIT
        return int(v*self.unit_cls.UNITS[unit])

    def __iadd__(self, other):
        if isinstance(other, (int, float)):
            self.value += self._display_unit_to_sp(other)
        elif isinstance(other, Dimen):
            self._check_same_type(other, yex.exception.CantAddError)
            self.value += other.value

        return self

    def __isub__(self, other):
        if isinstance(other, (int, float)):
            self.value -= self._display_unit_to_sp(other)
        elif isinstance(other, Dimen):
            self._check_same_type(other, yex.exception.CantSubtractError)
            self.value -= other.value

        return self

    def __imul__(self, other):
        self._check_numeric_type(other, yex.exception.CantMultiplyError)
        self.value = int(self.value * float(other))
        return self

    def __itruediv__(self, other):
        self._check_numeric_type(other, yex.exception.CantDivideError)
        self.value = int(self.value / float(other))
        return self

    def __add__(self, other):
        if other==0:
            # Zero is the only numeric value you can add to a Dimen.
            # This makes sum() work neatly.
            return self
        self._check_same_type(other, yex.exception.CantAddError)
        self._check_comparable(other)
        result = self.from_another(self, value=self.value + other.value)
        return result

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        self._check_same_type(other, yex.exception.CantSubtractError)
        result = self.from_another(self, value=self.value - other.value)
        return result

    def __mul__(self, other):
        self._check_numeric_type(other, yex.exception.CantMultiplyError)
        result = self.from_another(self, value=self.value * float(other))
        return result

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        self._check_numeric_type(other, yex.exception.CantDivideError)
        return self.from_another(self, value=self.value / float(other))

    def __neg__(self):
        return self.from_another(self, value=-self.value)

    def __pos__(self):
        return self.from_another(self, value=self.value)

    def __abs__(self):
        return self.from_another(self, value=abs(self.value))

    def __getstate__(self,
            always_list = False
            ):
        if self.infinity==0 and not always_list:
            return self.value
        else:
            return [self.value, self.infinity]

    def __setstate__(self, state):
        if isinstance(state, list):
            self.value, self.infinity = state
        elif isinstance(state, int):
            self.value = state
            self.infinity = 0
        else:
            raise TypeError()

        # unit_cls is always Dimen except in special cases from
        # particular classes, who know to reset it in their __setstate__
        self.unit_cls = Dimen
