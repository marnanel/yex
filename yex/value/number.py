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

        _value (int): The integer we represent.
    """

    def __init__(self, value=0):

        super().__init__()

        if isinstance(value, int):
            self._value = value
        elif isinstance(value, float):
            self._value = int(value)
        else:
            raise ValueError(
                    f"Numbers can only be numeric (and not {value})"
                    )

    @classmethod
    def from_tokens(cls, tokens):
        tokens = cls.prep_tokeniser(tokens)

        logger.debug(
                "let's look for a number from %s",
                tokens)

        value = cls.get_value_from_tokens(tokens)

        try:
            try:
                result = int(value)
            except ValueError:
                result = ord(value)
            except (TypeError, AttributeError):
                raise

        except:
            raise yex.exception.ExpectedButFoundError(
                    expected = cls.__name__,
                    value = value,
                    )

        logger.debug("found number from %s: %s",
                tokens,
                result)

        result = cls(result)

        return result

    @classmethod
    def from_another(cls, other, value=None):
        if value is None:
            value = other._value
        return cls(value)

    def __getstate__(self):
        return self._value

    def __repr__(self):
        return f'{self._value}'

    def __hash__(self):
        return self._value

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
        return self._value

    def __float__(self):
        return float(self._value)

    def __add__(self, other):
        self._check_numeric_type(other,
                "You can only add numeric values to %(us)s, "
                "not %(them)s.")
        result = self.from_another(self, value=self._value + int(other))
        return result

    def __sub__(self, other):
        self._check_numeric_type(other,
                "You can only subtract numeric values from %(us)s, "
                "not %(them)s.")
        result = self.from_another(self, value=self._value - int(other))
        return result

    def __mul__(self, other):
        self._check_numeric_type(other,
                "You can only multiply %(us)s by numeric values, "
                "not %(them)s.")
        result = self.from_another(self, value=self._value * int(other))
        return result

    def __div__(self, other):
        self._check_numeric_type(other,
                "You can only divide %(us)s by numeric values, "
                "not %(them)s.")
        return self.from_another(self, value = self._value // int(other))

    def __truediv__(self, other):
        self._check_numeric_type(other,
                "You can only divide %(us)s by numeric values, "
                "not %(them)s.")
        return self.from_another(self, value = self._value / int(other))

    def __neg__(self):
        return self.from_another(self, value = -float(self._value),)

    def __pos__(self):
        return self.from_another(self, value = self._value)

    def __abs__(self):
        return self.from_another(self, value = abs(self._value))

    def __setstate__(self, state):

        if hasattr(self, '_value'):
            raise yex.exception.AlreadyInitialisedError()

        if not isinstance(state, int):
            raise TypeError()

        self._value = state
