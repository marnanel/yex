class Value():

    def optional_negative_signs(self,
            tokeniser, tokens):
        """
        Handles a sequence of +, -, and spaces.
        Returns whether the sign is negative.
        """
        is_negative = False

        for c in tokens:

            if c.category==c.SPACE:
                continue
            elif c.category==c.OTHER:
                if c.ch=='+':
                    continue
                elif c.ch=='-':
                    is_negative = not is_negative
                    continue

            break

        tokeniser.push(c)

        return is_negative

    def unsigned_number(self,
            tokeniser, tokens,
            can_be_decimal = False,
            ):
        """
        Reads in an unsigned number, as defined on
        p265 of the TeXbook. If "can_be_decimal" is True,
        we can also read in a decimal constant instead, as defined
        on page 266 of the TeXbook.
        """

        base = 10
        accepted_digits = '0123456789'

        c = tokens.__next__()

        # XXX We need to deal with <coerced integer> too

        if c.category==c.OTHER:
            if c.ch=='`':
                # literal character, special case

                # "TeX does not expand this token, which should either
                # be a (character code, category code) pair,
                # or XXX an active character, or a control sequence
                # whose name consists of a single character.

                result = tokens.__next__()

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
                accepted_digits = '0123456789abcdef'
            elif c.ch=="'":
                base = 8
                accepted_digits = '01234567'
            elif c.ch in '0123456789.,':
                tokeniser.push(c)

        digits = ''
        for c in tokens:

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
                tokeniser.push(c)
                break

            elif c.category==c.SPACE:
                # One optional space, at the end
                break
            else:
                # we don't know what this is, and it's
                # someone else's problem
                tokeniser.push(c)
                break

        if digits=='':
            raise ValueError("Number had no digits")

        if can_be_decimal:
            try:
                return float(digits)
            except ValueError:
                # Catches weird cases like "." as a number,
                # which is valid and means zero.
                return 0
        else:
            return int(digits, base)

class Number(Value):

    def __init__(self, tokeniser, tokens):

        is_negative = self.optional_negative_signs(
                tokeniser, tokens)

        self.value = self.unsigned_number(
                tokeniser, tokens,
                )

        if is_negative:
            self.value = -self.value

    def __str__(self):
        return f'({self.value})'

def _units():
    """
    Returns a tuple:
       ( [dict of units, per p57 of the TeXbook],
         [set of first letters of those units],
         )
    The values are in millimetres.
    """
    units = {
            "cm": 10,                # Centimetres
            "mm": 1,                 # Millimetres
            "in": 25.4,              # Inches
            }

    units['pt'] = units['in']/72.27  # Point
    units['pc'] = units['pt']*12     # Pica
    units['bp'] = units['in']/72     # Big point
    units['dd'] = units['pt']*(1238/1157)  # Didot point
    units['cc'] = units['dd']/12     # Cicero
    units['sp'] = units['pt']/65536  # Big point

    first_letters = set(
            [k[0] for k in units.keys()])

    return (units, first_letters)

class Dimen(Value):

    UNITS, UNIT_FIRST_LETTERS = _units()

    def __init__(self, tokeniser, tokens):

        # See p266 of the TeXBook for the spec of a dimen.

        is_negative = self.optional_negative_signs(
                tokeniser, tokens)

        # there follows one of:
        #   - internal dimen
        #   - factor + unit of measure
        #   - internal glue

        # "factor" is like a normal integer (as in Number)
        # except that it may contain dots or commas for
        # decimal points. If it does, it can't begin with
        # a base specifier, and it can't be an internal integer.
        factor = self.unsigned_number(
                tokeniser, tokens,
                can_be_decimal = True,
                )


        # units of measure that can be preceded by "true":
        #   pt | pc | in | bp | cm | mm | dd | cc | sp
        # internal units of measure that can't:
        #   em | ex
        #   and <internal integer>, <internal dimen>, and <internal glue>.

class Macro:

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def syntax(self):
        return []

    def get_params(self, tokeniser, tokens):
        raise ValueError("superclass does nothing useful in itself")

    def __call__(self):
        raise ValueError("superclass does nothing useful in itself")

class Catcode(Macro):

    def get_params(self, tokeniser, tokens):
        n = Number(tokeniser, tokens)
        raise KeyError(n)

    def __call__(self):
        raise ValueError("catcode called")

def add_macros_to_state(state):
    state.add_state(
            'macro',
            names(),
            )

def names():

    result = dict([
            (name.lower(), value) for
            (name, value) in globals().items()
            if value.__class__==type and
            value!=Macro and
            issubclass(value, Macro)
            ])

    return result
