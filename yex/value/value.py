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
            could_be_float = False,
            could_be_codepoint = False,
            ):
        r"""
        Reads in a number, as defined on p265 of the TeXbook.

        If we find a control which is the name of a register,
        such as "\dimen2", we return the value of that register.
        This means that the function might not return int or float
        (it might return Number or Dimen, for example).

        Arguments:
            tokens (Expander): where to find the number
            could_be_float (bool): if True, we can also read in a fractional
                decimal constant instead, as defined on p266 of the TeXbook,
                such as "123.456". If we find this, we will return it
                as a float.
            could_be_codepoint (bool): if True, and if the
                first thing read from "tokens" is a single-character string,
                return the codepoint of that string. This is usually
                not what you want.

        Returns:
            int, in the general case. If could_be_float==True, and we found
            a fractional number, we return float. If we found the name of
            a register, we return the value of that register.
        """

        base = 10
        accepted_digits = string.digits
        is_negative = False
        digits = ''

        us = tokens.location

        for c in tokens.another(on_eof='raise', level='expanding'):
            logger.debug(
                    "%s: -- unsigned number, at the start: %s, of type %s",
                    us, c, type(c))

            if isinstance(c, (int, float)):
                logger.debug(
                        "%s:  -- found %s",
                        us, c)
                return c
            elif isinstance(c, str) and not digits and could_be_codepoint:
                result = ord(c)
                logger.debug(
                        "%s:  -- str of length 1; returning its codepoint: %s",
                        us, result)
                return result

            elif isinstance(c, yex.parse.Other):
                if c.ch=='`':
                    # literal character, special case

                    # "TeX does not expand this token, which should either
                    # be a (character code, category code) pair,
                    # or an active character, or a control sequence
                    # whose name consists of a single character.

                    result = tokens.next(
                            level='deep',
                            on_eof='raise')

                    if isinstance(result, yex.parse.Control):
                        logger.debug(
                                "%s: reading value; backtick+control, %s",
                                us, result)

                        name = result.name
                        if len(name)!=1:
                            raise yex.exception.LiteralControlTooLongError(
                                    name = result,
                                    )
                        return ord(name[0])
                    elif isinstance(result, yex.parse.Token):
                        return ord(result.ch)
                    else:
                        raise yex.exception.ImproperAlphabeticConstantError(
                                problem = result,
                                )

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
                yex.control.Control,
                )):

                if isinstance(c, yex.control.Control):
                    referent = c
                else:
                    referent = tokens.doc[c.ch]

                if hasattr(referent, 'is_array') and referent.is_array:
                    element = referent.get_element_from_tokens(tokens)
                    logger.debug("%s:    -- array element: %s",
                            us, element)
                    return element.value

                elif isinstance(referent, (
                    yex.value.Dimen,
                    yex.value.Glue,
                    yex.value.Muglue,
                    yex.value.Tokenlist,
                    )):
                    return referent

                elif isinstance(referent, (int, float)):
                    return referent

                elif isinstance(referent, str) and len(referent)==1:
                    return ord(referent)

                elif hasattr(referent, 'value'):

                    result = referent.value

                    logger.debug(
                            ("%s:  -- token is %s, which is %s, "
                            "which has the value %s"),
                            us, c, referent, result)

                    return result

            elif isinstance(c, yex.parse.Space):
                continue

            else:
                raise yex.exception.ExpectedNumberError(
                        problem=c,
                        )

        digits += tokens.get_digit_sequence(
                accept_ch = accepted_digits,
                accept_decimal_point = (could_be_float and base==10),
                )

        logger.debug(
                "%s:  -- result is %s",
                us,
                repr(digits),
                )

        if digits=='':
            raise yex.exception.ExpectedNumberError(
                    problem = c,
                    )

        if is_negative:
            digits = f'-{digits}'

        if could_be_float:
            try:
                return float(digits.replace(',','.'))
            except ValueError as e:
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

    @property
    def value(self):
        return self._value

    def __getstate__(self):
        raise NotImplementedError()

    def __setstate__(self, value):
        raise NotImplementedError(
                # this is a real nuisance to find, so let's have a message
                f'Unimplemented __setstate__ for {self.__class__.__name__}'
                )

    @classmethod
    def from_serial(cls, state):
        result = cls.__new__(cls)
        result.__setstate__(state)
        return result
