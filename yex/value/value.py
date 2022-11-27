import string
import yex.exception
import logging

logger = logging.getLogger('yex.general')

class Value:
    """
    Abstract superclass of Number, Dimen, Glue, Muglue, and Tokenlist.
    """

    @classmethod
    def prep_tokeniser(cls, tokens):
        return tokens.another(
                level = 'reading',
                on_eof = 'none',
                )

    @classmethod
    def get_value_from_tokens(cls,
            tokens,
            can_be_decimal = False,
            ):
        r"""
        Reads in a number, as defined on
        p265 of the TeXbook. If "can_be_decimal" is True,
        we can also read in a decimal constant instead, as defined
        on page 266 of the TeXbook.

        If we find a control which is the name of a register,
        such as "\dimen2", we return the value of that register.
        This means that the function might not return int or float
        (it might return Number or Dimen).
        """

        base = 10
        accepted_digits = string.digits
        is_negative = False
        digits = ''

        for c in tokens.another(on_eof='raise', level='deep'):
            logger.debug(
                    "  -- unsigned number, at the start: %s, of type %s",
                    c, type(c))

            if isinstance(c, yex.control.C_Control) and c.is_queryable:
                return c.value

            elif not isinstance(c, yex.parse.Token):
                return c

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
                            raise yex.exception.LiteralControlTooLongError(
                                    name = result,
                                    )
                        return ord(name[0])
                    else:
                        return ord(result.ch)

                elif c.ch=='"':
                    base = 16
                    accepted_digits = string.hexdigits
                    break
                elif c.ch=="'":
                    base = 8
                    accepted_digits = string.octdigits
                    break
                elif c.ch in string.digits+'.,':
                    digits = c.ch
                    break
                elif c.ch=='+':
                    continue
                elif c.ch=='-':
                    is_negative = not is_negative
                    continue

            elif isinstance(c, (
                yex.parse.Control,
                yex.parse.Active,
                )):
                logger.debug(
                        "  -- token is %s, which is a control; evaluating it",
                        c)

                tokens.push(c)

                result = tokens.next(
                        level='querying',
                        )

                logger.debug(
                        "  -- %s produced: %s",
                        c, result)

                if isinstance(result, str) and len(result)==1:
                    result = ord(result)
                    logger.debug(
                            "    -- returning its codepoint: %s",
                            result)

                return result

            elif isinstance(c, yex.parse.Space):
                continue

            else:
                raise ValueError(repr(c))

        for c in tokens.another(on_eof='exhaust'):
            if not isinstance(c, yex.parse.Token):
                logger.debug(
                        "  -- unsigned number, middle: found %s, of type %s",
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
                repr(digits))

        if digits=='':
            raise yex.exception.ExpectedNumberError(
                    problem = repr(c),
                    )

        if is_negative:
            digits = f'-{digits}'

        if can_be_decimal:
            try:
                return float(digits)
            except ValueError:
                # Catches weird cases like "." as a number,
                # which is valid and means zero.
                return 0.0
        else:
            return int(digits, base)

    def _check_same_type(self, other, exc):
        """
        Checks two values are of the same type.
        If other is exactly the same type as self, does nothing.
        Otherwise raises an instance of the exception class "exc"
        with us=self and them=other.

        Maybe this should work with subclasses too, idk. It
        doesn't actually make a difference for what we're doing.
        """
        if type(self)!=type(other):
            raise exc(
                    us = self,
                    them = other,
                    )

    def _check_numeric_type(self, other, exc):
        """
        Checks that "other" is numeric. Dimens don't count.

        If "other" is numeric, does nothing.
        Otherwise raises an instance of the exception class "exc",
        with them=other.
        """
        if not isinstance(other, (int, float, yex.value.Number)):
            raise exc(
                    us = self,
                    them = other,
                    )

    def __getstate__(self):
        raise NotImplementedError()

    def __setstate__(self):
        raise NotImplementedError()

    @classmethod
    def from_serial(cls, state):
        result = cls.__new__(cls)
        result.__setstate__(state)
        return result
