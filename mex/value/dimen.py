import string
import functools
import mex.exception
import mex.parse
import logging
from mex.value.value import Value

commands_logger = logging.getLogger('mex.commands')

SP_TO_PT = 1/65536.0

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
        """
        Reads the next one or two tokens.

        If they're the name of a unit, as listed in self.unit_obj.UNITS,
        we return that name as a string.

        If the first token is any kind of control, we return that control
        without consuming anything after it.

        Otherwise, we raise an error.
        """

        c1 = self.tokens.next()
        c2 = None

        if c1 is not None and c1.category==c1.LETTER:
            if c1.ch in self.unit_obj.UNIT_FIRST_LETTERS:

                c2 = self.tokens.next()

                if c2.category==c2.LETTER:

                    unit = c1.ch+c2.ch

                    if unit in self.unit_obj.UNITS:
                        commands_logger.debug("reading Dimen: unit is %s",
                                unit)
                        return unit

        if c1 is not None:

            commands_logger.debug("reading Dimen: that wasn't a unit")

            if isinstance(c1, mex.parse.Token) and \
                    c1.category==c1.CONTROL:
                return c1

            problem = c1.ch
            if c2 is not None:
                problem += c2.ch
        else:
            problem = 'end of file'

        raise mex.exception.ParseError(
                f"dimensions need a unit (found {problem})")

    def __init__(self, t=0,
            unit = None,
            infinity = 0,
            can_use_fil = False,
            unit_obj = None,
            ):

        self.unit_obj = unit_obj or self

        # See p266 of the TeXBook for the spec of a dimen.

        if isinstance(t, mex.parse.Tokenstream):
            super().__init__(t)

            self._parse_dimen(
                    t,
                    can_use_fil,
                    )

        else:
            super().__init__(None)
            self.value = float(t)
            self.infinity = infinity

            if unit is None:
                unit = self.unit_obj.DISPLAY_UNIT

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
        import mex.control

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
            mex.control.C_Parameter,
            )):

            if is_negative:
                raise mex.exception.ParseError(
                        "there is no unary negation of registers")

            if isinstance(factor, (
                mex.register.Register,
                mex.control.C_Parameter,
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
        if isinstance(unit, str):
            unit_size = self.unit_obj.UNITS[unit]
        else:
            tokens.push(unit)
            n = mex.value.Dimen(tokens)
            unit_size = n.value

            commands_logger.debug(
                    "unit size was a reference: %g*%g (%dsp)",
                    factor, n, unit_size)

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
                current_font = self.tokens.state['_font']

                if unit=='em':
                    unit_size = current_font[6].value # quad width
                elif unit=='ex':
                    unit_size = current_font[5].value # x-height
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
        if self.infinity!=0:
            return self.value
        return self.value / self.unit_obj.UNITS[self.unit_obj.DISPLAY_UNIT]

    def __eq__(self, other):
        return float(self)==float(other)

    def __lt__(self, other):
        return float(self)<float(other)

    def __int__(self):
        """
        This returns the length in points (or whatever the display unit is)..

        If you want it in scaled points, access the "value" attribute
        directly.
        """
        return int(float(self))
