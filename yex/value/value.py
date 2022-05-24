import string
import yex.exception
import logging

logger = logging.getLogger('yex.general')

class Value:
    """
    Abstract superclass of Number, Dimen, Glue, Muglue, and Tokenlist.
    """

    def prep_tokeniser(self, tokens):
        return tokens.another(
                level = 'reading',
                on_eof = 'none',
                )

    def optional_negative_signs(self, tokens):
        """
        Handles a sequence of +, -, and spaces.
        Returns whether the sign is negative.
        """
        is_negative = False
        c = None

        # This is the only place in Value where we run the expander
        # at a level above "running". That's because we're right at
        # the beginning, and this is where you get macros etc.
        for c in tokens.another(level='querying'):
            logger.debug("  -- possible negative signs: %s", c)

            if c is None or not isinstance(c, yex.parse.Token):
                break
            elif isinstance(c, yex.parse.Space):
                continue
            elif isinstance(c, yex.parse.Other):
                if c.ch=='+':
                    continue
                elif c.ch=='-':
                    is_negative = not is_negative
                    continue

            break

        if c is not None:
            logger.debug(
                    "  -- possible negative signs: push back %s",
                    c)
            tokens.push(c)

        return is_negative

    def unsigned_number(self,
            tokens,
            can_be_decimal = False,
            ):
        r"""
        Reads in an unsigned number, as defined on
        p265 of the TeXbook. If "can_be_decimal" is True,
        we can also read in a decimal constant instead, as defined
        on page 266 of the TeXbook.

        If we find a control which is the name of a register,
        such as "\dimen2", we return the value of that register.
        This means that the function might not return int or float
        (it might return Number or Dimen).
        """

        def maybe_dereference(x):
            if isinstance(x,
                    (Value, float, int),
                    ):
                return x

            try:
                # maybe it's a control or a register
                v = x.value
            except AttributeError:
                raise yex.exception.ParseError(
                        f"Expected a number but found {x}")

            logger.debug(
                    "    -- %s.value==%s",
                    x, v)
            if isinstance(v, str) and len(v)==1:
                return ord(v)
            else:
                return v

        base = 10
        accepted_digits = string.digits

        c = tokens.next()

        logger.debug(
                "  -- received %s %s",
                c, type(c))

        if not isinstance(c, yex.parse.Token):
            return maybe_dereference(c)

        elif isinstance(c, yex.parse.Other):
            if c.ch=='`':
                # literal character, special case

                # "TeX does not expand this token, which should either
                # be a (character code, category code) pair,
                # or XXX an active character, or a control sequence
                # whose name consists of a single character.

                result = tokens.next(
                        level='deep',
                        on_eof='raise')

                if isinstance(result, yex.parse.Control):
                    logger.debug(
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

        elif isinstance(c, (
            yex.parse.Control,
            yex.parse.Active,
            )):
            logger.debug(
                    "  -- token is %s, which is a control; evaluating it",
                    c)

            tokens.push(c)

            result = tokens.next(
                    level='expanding',
                    )

            logger.debug(
                    "  -- %s produced: %s",
                    c, result)

            return maybe_dereference(result)

        logger.debug(
                "  -- ready to read literal, accepted==%s",
                accepted_digits)

        digits = ''
        for c in tokens:
            if not isinstance(c, yex.parse.Token):
                logger.debug(
                        "  -- found %s, of type %s",
                        c, type(c))
                tokens.push(c)
                break
            elif isinstance(c, (yex.parse.Other, yex.parse.Letter)):
                symbol = c.ch.lower()
                if symbol in accepted_digits:
                    digits += c.ch
                    logger.debug(
                            "  -- accepted; digits==%s",
                            digits)
                    continue

                elif symbol in '.,':
                    if can_be_decimal and base==10:
                        logger.debug(
                                "  -- decimal point")
                        if '.' not in digits:
                            # XXX What does TeX do if there are
                            # multiple decimal points in the same
                            # number? The spec allows it.
                            digits += '.'
                        continue

                # it's an unknown symbol; stop
                logger.debug(
                        "  -- found %s",
                        c)
                tokens.push(c)
                break

            elif isinstance(c, yex.parse.Space):
                # One optional space, at the end

                logger.debug(
                        "  -- final space; stop")

                break
            else:
                # we don't know what this is, and it's
                # someone else's problem

                logger.debug(
                        "  -- don't know; stop: %s",
                        c)

                tokens.push(c)
                break

        logger.debug(
                "  -- result is %s",
                digits)

        if digits=='':
            raise yex.exception.ParseError(
                    f"Expected a number but found: {str(c)}")

        if can_be_decimal:
            try:
                return float(digits)
            except ValueError:
                # Catches weird cases like "." as a number,
                # which is valid and means zero.
                return 0.0
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
