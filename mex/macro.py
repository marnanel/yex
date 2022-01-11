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

class Number(Value):

    def __init__(self, tokeniser, tokens):

        # See p265 of the TeXBook for the spec of a number.

        is_negative = False
        base = 10
        accepted_digits = '0123456789'

        is_negative = self.optional_negative_signs(
                tokeniser, tokens)
        
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

                    self.value = ord(name[0])
                else:
                    self.value = ord(result.ch)

                return

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

        self.value = int(digits, base)

        if is_negative:
            self.value = -self.value

    def __str__(self):
        return f'({self.value})'

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
