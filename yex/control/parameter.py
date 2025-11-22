r"""
Types of parameters.

The parameters themselves live in yex.keyword.parameter.
"""
import os
import yex.value
import yex.mode
import yex.exception
import yex.font
import datetime
import yex.logging
from yex.control import Unexpandable

logger = yex.logging.getLogger('control')

class Parameter(Unexpandable):
    r"""
    Parameters are a specialised form of
    [control](yex.control.Control.md),
    with a value and a type.
    For example,
    [`\hsize`](yex.keyword.Hsize.md) holds the width of
    the current line, which is a
    [dimen](yex.value.Dimen.md).

    Like all controls, parameters can be called. This is equivalent
    to assigning them a value. For example,
    ```
        \hsize 3pt
    ```
    assigns the value 3pt to `\hsize`.

    Each [document](yex.Document.md) creates at most one
    instance of each parameter class.

    There is a subclass of Parameter for each type:

    - [NumberParameter.md](yex.control.NumberParameter.md) for numbers,
    - - [TimeParameter.md](yex.control.TimeParameter.md) for numbers
        related to the current time,
    - [DimenParameter.md](yex.control.DimenParameter.md) for dimens,
    - [GlueParameter.md](yex.control.NumberParameter.md) for glue,
    - [MuglueParameter.md](yex.control.NumberParameter.md) for muglue, and
    - [TokenlistParameter.md](yex.control.NumberParameter.md) for tokenlists.

    The parameter classes themselves are subclasses of these.

    TeXbook:
        pp269-271

    Attributes:
        our_type (Type): the class we represent, in the form we use
            to store it. If this is a tuple, we can contain multiple types;
            the first one listed will be used to initialise a new control.
        initial_value (Any): the value this parameter has on startup
        do_not_initialise (bool): if True, _value will not be initialised.
            If False (the default), _value will be initialised with a new
            instance of our_type (or our_type[0] if our_type is a tuple).
        is_outer (bool): not applicable, and always False
        is_queryable (bool): not applicable, and always True

    """
    our_type = None
    initial_value = 0
    is_outer = False
    do_not_initialise = False
    is_queryable = True

    def __init__(self, value=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self._value = value
        elif self.do_not_initialise:
            pass
        elif isinstance(self.initial_value, self.our_type):
            self._value = self.initial_value
        elif isinstance(self.our_type, tuple):
            self._value = self.our_type[0](self.initial_value)
        else:
            self._value = self.our_type(self.initial_value)

    # The property setter/getter methods are implemented weirdly
    # to make sure inheritance works properly. Python has a baroque
    # structure for this.
    @property
    def value(self):
        return self._get_value()

    @value.setter
    def value(self, v):
        self._set_value(v)

    def _get_value(self):
        return self._value

    def _set_value(self, n):
        if not isinstance(n, self.our_type):
            raise yex.exception.ExpectedButFoundError(
                    expected = self.our_type.__name__,
                    found = n,
                    )

        self._value = n

    def set_from(self, parser: 'yex.parse.Parser'):
        """
        Sets the value from a token stream.
        """
        parser.eat_optional_char('=')
        v = self.our_type.from_parser(parser)
        logger.debug("Setting %s=%s",
                self, v)
        self.value = v

    def get_the(self, parser: 'yex.parse.Parser') -> str:
        r"""
        Finds a representation of this parameter's value, as used by
        the control \the.

        Returns:
            a string representing the value.
        """
        if isinstance(self.value, str):
            return self.value
        else:
            return repr(self.value)

    def __call__(self, parser: 'yex.parse.Parser'):
        self.set_from(parser)

    def __repr__(self):
        try:
            return '['+repr(self._get_value())+']'
        except Exception as e:
            return '[broken '+self.__class__.__name__+': '+repr(e)+']'

    def __int__(self):
        return int(self._value)

    def __getstate__(self):
        result = {
                'control': self.name,
                }
        value = self._get_value()
        if value != self.initial_value:

            if hasattr(value, '__getstate__'):
                value = value.__getstate__()

            result['value'] = value

        return result

class NumberParameter(Parameter):
    r"""
    Number parameters.

    Parameter controls whose value is an integer. The numbers are stored
    as an `int` internally, but we set and get them as `yex.value.Number`s.
    """
    our_type = int

    def set_from(self, parser: 'yex.parse.Parser'):
        parser.eat_optional_char('=')
        number = yex.value.Number.from_parser(parser)
        self.value = number.value
        logger.debug("Setting %s=%s",
                self, self.value)

    def _set_value(self, n):
        self._value = int(n)

class DimenParameter(Parameter):
    r"""
    Dimen parameters.

    Parameter controls whose value is a Dimen-- that is, a physical length.
    """
    our_type = yex.value.Dimen

class GlueParameter(Parameter):
    r"""
    Glue parameters.

    Parameter controls whose value is a Glue-- the distance between two
    items on a page, which can stretch or shrink.
    """
    our_type = yex.value.Glue

class MuglueParameter(GlueParameter):
    r"""
    Muglue parameters.

    Parameter controls whose value is a Muglue-- a special kind of glue
    used for setting maths.
    """
    our_type = yex.value.Muglue

class TokenlistParameter(Parameter):
    r"""
    Tokenlist parameters.

    Parameter controls whose value is a Tokenlist-- a list of symbols.
    """
    our_type = yex.value.Tokenlist
    initial_value = []

    def _set_value(self, v):
        if isinstance(v, yex.value.Tokenlist):
            self._value = yex.value.Tokenlist.from_another(v)
        elif isinstance(v, (list, str)):
            self._value = yex.value.Tokenlist(v)
        else:
            raise yex.exception.ExpectedButFoundError(
                    expected = 'Tokenlist',
                    found = v,
                    )

class TimeParameter(NumberParameter):

    time_loaded = datetime.datetime.now()

    def __init__(self, **kwargs):
        value = self._extract_field(self.time_loaded)
        super().__init__(value, **kwargs)

    def _extract_field(value):
        raise NotImplementedError()
