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
            decimal_constant = False,
            ):
        """
        Reads in an unsigned number, as defined on
        p265 of the TeXbook. If "decimal_constant" is True,
        reads in a decimal constant instead, as defined
        on page 266 of the TeXbook.
        """

        if decimal_constant:
            accepted_digits = '0123456789,.'
        else:
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
                elif c.ch>='0' and c.ch<='9':
                    tokeniser.push(c)

        digits = ''
        for c in tokens:

            if c.category in (c.OTHER, c.LETTER) and \
                    c.ch.lower() in accepted_digits:
                digits += c.ch
                continue
            elif c.category==c.SPACE:
                # One optional space, at the end
                break
            else:
                tokeniser.push(c)
                break

        if digits=='':
            raise ValueError("Number had no digits")

        if decimal_constant:
            try:
                return float(digits.replace(',','.'))
            except ValueError:
                # Catches weird cases like "." as a number,
                # which is valid and means zero.
                #
                # XXX What about numbers containing multiple
                # decimal points? What does TeX do?
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

class Dimen(Value):
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
