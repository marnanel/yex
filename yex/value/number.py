import string
import functools
import yex.exception
import yex.parse
import logging
from yex.value.value import Value

commands_logger = logging.getLogger('yex.commands')

@functools.total_ordering
class Number(Value):

    def __init__(self, v=0):

        super().__init__()

        if isinstance(v, int):
            self._value = v
            return
        elif isinstance(v, float):
            self._value = int(v)
            return

        tokens = self.prep_tokeniser(v)

        commands_logger.debug(
                "let's look for a number from %s",
                tokens)

        is_negative = self.optional_negative_signs(tokens)

        self._value = self.unsigned_number(tokens)

        if not isinstance(self._value, int):
            if is_negative:
                raise TypeError(
                        "unary negation only works on literals")
        try:
            self._value = int(self._value)
        except (TypeError, AttributeError):
            raise yex.exception.ParseError(
                    f"expected a Number, but found {self._value}")

        if is_negative:
            self._value = -self._value

        commands_logger.debug("found number from %s: %s",
                tokens,
                self._value)

    def __repr__(self):
        return f'{self._value}'

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, x):
        self._check_numeric_type(x,
                "Numbers can only be numeric (not %(them)s).")

        self._value = int(x)

    def __hash__(self):
        return self.value

    def __eq__(self, other):
        self._check_numeric_type(other,
                "Numbers can only be compared with numbers (not %(them)s).")

        return self.value==int(other)

    def __lt__(self, other):
        self._check_numeric_type(other,
                "Numbers can only be compared with numbers (not %(them)s).")

        return self.value<int(other)

    def __int__(self):
        return self.value

    def __float__(self):
        return float(self.value)