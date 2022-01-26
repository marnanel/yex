class Value():

    def __init__(self, tokens):
        self.tokens = tokens

    def optional_negative_signs(self):
        """
        Handles a sequence of +, -, and spaces.
        Returns whether the sign is negative.
        """
        is_negative = False

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
        accepted_digits = '0123456789'

        c = self.tokens.__next__()

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
                accepted_digits = '0123456789abcdef'
            elif c.ch=="'":
                base = 8
                accepted_digits = '01234567'
            elif c.ch in '0123456789.,':
                self.tokens.push(c)

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

class Number(Value):

    def __init__(self, tokens):

        super().__init__(tokens)

        is_negative = self.optional_negative_signs()

        self.value = self.unsigned_number()

        if is_negative:
            self.value = -self.value

    def __str__(self):
        return f'({self.value})'

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
            }

    UNIT_FIRST_LETTERS = set(
            [k[0] for k in UNITS.keys()])

    def optional_unit_of_measurement(self):

        c1 = self.tokens.__next__()
        c2 = None

        if c1.category==c1.LETTER:
            if c1.ch in self.UNIT_FIRST_LETTERS:

                c2 = self.tokens.__next__()

                if c2.category==c2.LETTER:

                    unit = c1.ch+c2.ch

                    if unit in self.UNITS:
                        return self.UNITS[unit]

        if c2 is not None:
            self.tokens.push(c2)

        self.tokens.push(c1)
        return None

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

        # units of measure that can be preceded by "true":
        #   pt | pc | in | bp | cm | mm | dd | cc | sp
        # internal units of measure that can't:
        #   em | ex
        #   and <internal integer>, <internal dimen>, and <internal glue>.

        is_true = self.optional_string(
                'true')

        unit = self.optional_unit_of_measurement(
                )

        self.value = int(factor*unit)

        if not is_true:
            self.value *= self.tokens.state['mag'].value
            self.value /= 1000

        if is_negative:
            self.value = -self.value
