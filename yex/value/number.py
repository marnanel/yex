import string
import functools
import yex.exception
import yex.parse
import logging
from yex.value.value import Value

logger = logging.getLogger('yex.general')

@functools.total_ordering
class Number(Value):
    """
    An integer.

    Attributes:

        _value (int): The integer we represent. This is kept as a private
            attribute so that we can check what people are setting us to.
    """

    def __init__(self, v=0):

        super().__init__()

        if isinstance(v, int):
            self._value = v
            return
        elif isinstance(v, float):
            self._value = int(v)
            return

        tokens = self.prep_tokeniser(v)

        logger.debug(
                "let's look for a number from %s",
                tokens)

        is_negative = self.optional_negative_signs(tokens)

        self._value = self.unsigned_number(tokens)

        try:
            self._value = int(self._value)
        except (TypeError, AttributeError):
            raise yex.exception.ParseError(
                    f"expected a Number, but found {self._value}")

        if is_negative:
            self._value = -self._value

        logger.debug("found number from %s: %s",
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
        try:
            return self.value==int(other)
        except TypeError:
            return False

    def __lt__(self, other):
        self._check_numeric_type(other,
                "Numbers can only be compared with numbers (not %(them)s).")

        return self.value<int(other)

    def __int__(self):
        return self.value

    def __float__(self):
        return float(self.value)

    def __iadd__(self, other):
        self._check_numeric_type(other,
                "You can only add numeric values to %(us)s, "
                "not %(them)s.")
        self.value += other.value
        return self

    def __isub__(self, other):
        self._check_numeric_type(other,
                "You can only subtract numeric values from %(us)s, "
                "not %(them)s.")
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
        self._check_numeric_type(other,
                "You can only add numeric values to %(us)s, "
                "not %(them)s.")
        result = self._make_similar(float(self) + float(other))
        return result

    def __sub__(self, other):
        self._check_numeric_type(other,
                "You can only subtract numeric values from %(us)s, "
                "not %(them)s.")
        result = self._make_similar(float(self) - float(other))
        return result

    def __mul__(self, other):
        self._check_numeric_type(other,
                "You can only multiply %(us)s by numeric values, "
                "not %(them)s.")
        result = self._make_similar(float(self) * float(other))
        return result

    def __truediv__(self, other):
        self._check_numeric_type(other,
                "You can only divide %(us)s by numeric values, "
                "not %(them)s.")
        return self._make_similar(
                value = float(self) / float(other),
                )

    def __neg__(self):
        return self._make_similar(
                value = -float(self),
                )

    def __pos__(self):
        return self._make_similar(value=float(self))

    def __abs__(self):
        return self._make_similar(value=abs(self))

    def _make_similar(self, value):
        return self.__class__(value)
