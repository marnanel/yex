import string
import yex.exception
import yex.parse
import logging

commands_logger = logging.getLogger('yex.commands')

class Value():

    def prep_tokeniser(self, tokens):
        return tokens.child(
                expand = False,
                on_eof = tokens.EOF_RETURN_NONE,
                )

    def optional_negative_signs(self, tokens):
        """
        Handles a sequence of +, -, and spaces.
        Returns whether the sign is negative.
        """
        is_negative = False
        c = None

        for c in tokens:
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
            tokens.push(c)

        return is_negative

    def unsigned_number(self,
            tokens,
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

        c = tokens.next()

        if c is None:
            pass # eof
        elif c.category==c.OTHER:
            if c.ch=='`':
                # literal character, special case

                # "TeX does not expand this token, which should either
                # be a (character code, category code) pair,
                # or XXX an active character, or a control sequence
                # whose name consists of a single character.

                result = tokens.next(expand=False,
                        on_eof=tokens.EOF_RAISE_EXCEPTION)

                if result.category==result.CONTROL:
                    commands_logger.debug(
                            "reading value; backtick+control, %s",
                            result)

                    name = result.name
                    if len(name)!=1:
                        raise yex.exception.ParseError(
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
                tokens.push(c)

        elif c.category==c.CONTROL:

            name = c.name

            result = tokens.doc.get(
                    name,
                    tokens=tokens,
                    )

            commands_logger.debug(
                    "  -- name==%s, ==%s",
                    name,
                    result)

            if result is None:
                raise yex.exception.MacroError(
                        f"there is no macro called {name}")

            if isinstance(result, yex.control.C_Defined):
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
        for c in tokens.child(expand=False):
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
                tokens.push(c)
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
                tokens.push(c)
                break

        if digits=='':
            if c is None:
                raise yex.exception.ParseError(
                        f"Expected a number but found EOF")
            else:
                raise yex.exception.ParseError(
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

    def _check_same_type(self, other, error_message):
        """
        If other is exactly the same type as self, does nothing.
        Otherwise raises TypeError.

        Maybe this should work with subclasses too, idk. It
        doesn't actually make a difference for what we're doing.
        """
        if type(self)!=type(other):
            raise TypeError(
                    error_message % {
                        'us': self.__class__.__name__,
                        'them': other.__class__.__name__,
                        })

    def _check_numeric_type(self, other, error_message):
        """
        Checks that "other" is numeric. Dimens don't count.
        """

        from yex.value.number import Number

        if not isinstance(other, (int, float, Number)):
            raise TypeError(
                    error_message % {
                        'us': self.__class__.__name__,
                        'them': other.__class__.__name__,
                        })

    def __iadd__(self, other):
        self._check_same_type(other,
                "Can't add %(them)s to %(us)s.")
        self.value += other.value
        return self

    def __isub__(self, other):
        self._check_same_type(other,
                "Can't subtract %(them)s from %(us)s.")
        self.value -= other.value
        return self

    def __imul__(self, other):
        self._check_numeric_type(other,
                "You can only multiply %(us)s by numeric values, "
                "not %(them)s.")
        self.value *= float(other)
        return self

    def __itruediv__(self, other):
        self._check_numeric_type(other,
                "You can only divide %(us)s by numeric values, "
                "not %(them)s.")
        self.value /= float(other)
        return self

    def __add__(self, other):
        self._check_same_type(other,
                "Can't add %(them)s to %(us)s.")
        result = self.__class__(float(self) + float(other))
        return result

    def __sub__(self, other):
        self._check_same_type(other,
                "Can't subtract %(them)s from %(us)s.")
        result = self.__class__(float(self) - float(other))
        return result

    def __mul__(self, other):
        self._check_numeric_type(other,
                "You can only multiply %(us)s by numeric values, "
                "not %(them)s.")
        result = self.__class__(float(self) * float(other))
        return result

    def __truediv__(self, other):
        self._check_numeric_type(other,
                "You can only divide %(us)s by numeric values, "
                "not %(them)s.")
        result = self.__class__(float(self) / float(other))
        return result
