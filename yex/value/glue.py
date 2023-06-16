import string
import yex.exception
import yex.parse
import logging
from yex.value.value import Value
from yex.value.dimen import Dimen

logger = logging.getLogger('yex.general')

class Glue(Value):
    """
    A space between the smaller Boxes inside a Box.

    A Glue has space, stretch, and shrink.

    The specifications for Glue may be found in ch12
    of the TeXbook, beginning on page 69.
    """

    def __init__(self,
            space = 0.0,
            space_unit = None,
            stretch = 0,
            stretch_unit = None,
            shrink = 0,
            shrink_unit = None,
            ):

        """
        space, stretch, and shrink are all numeric. They're passed to
        Dimen()'s constructor along with the unit supplied.
        They may also be Dimens, in which case their unit must not
        be specified.

        space_unit, stretch_unit, and shrink_unit are the units for
        the space, stretch, and shrink parameters, respectively.
        In addition to the usual possibilities,
        stretch_unit and shrink_unit may be 'fil', 'fill', or 'filll'
        for infinities.
        """

        args = locals()
        def _to_dimen(arg, can_be_infinite):
            length = args[arg]
            unit = args[f'{arg}_unit']

            if isinstance(length, Dimen):
                if unit is not None:
                    raise ValueError(
                            f'"{arg}" was a Dimen, '
                            f'but {arg}_unit was not None'
                            )

                if not can_be_infinite and length.infinity!=0:
                    raise ValueError(
                            f'"{arg}" must be finite'
                            )
                return Dimen.from_another(length)
            else:
                try:
                    length = float(length)
                except TypeError:
                    raise ValueError(
                            f'{arg}=={length} must be numeric or Dimen '
                            f'(and not {type(length)})'
                            )

                if can_be_infinite:
                    inf = {'can_use_fil': True}
                else:
                    inf = {}

                return Dimen(
                        float(length),
                        unit = unit,
                        **inf)

        self._space   = _to_dimen('space',   False)
        self._stretch = _to_dimen('stretch', True)
        self._shrink  = _to_dimen('shrink',  True)

    @classmethod
    def from_another(cls, another):
        result = cls.__new__(cls)
        result._space = Dimen.from_another(another._space)
        result._stretch = Dimen.from_another(another._stretch)
        result._shrink = Dimen.from_another(another._shrink)
        return result

    @property
    def space(self):
        return self._space
    @property
    def stretch(self):
        return self._stretch
    @property
    def shrink(self):
        return self._shrink

    @classmethod
    def _raise_parse_error(cls):
        """
        I'm sorry, I haven't a Glue
        """
        raise ValueError(f'Expected a {cls.__name__}')

    @classmethod
    def from_tokens(cls,
            tokens,
            ):
        """
        Factory method: parses a Glue from a token stream.

        See p267 of the TeXBook for the spec of a dimen.

        Args:
            tokens: the token stream

        Returns:
            A new Glue, constructed according to the tokens found.
        """

        for handler in [
                cls._parse_glue_variable,
                cls._parse_glue_literal,
                ]:

            result = handler(tokens)

            if result is not None:
                return result

        cls._raise_parse_error()

    @classmethod
    def _parse_glue_variable(cls, tokens):
        r"""
        Attempts to copy a new Glue from a variable containing a Glue.

        We're looking for optional negative signs, and then one of
           - actual preexisting Glue
           - glue parameter
           - \lastskip
           - a token defined with \skipdef
           - a \skipNNN register

        Returns the value if it succeeds. Otherwise, backs up to where
        it started and returns None.
        """

        new_fields = {}

        logger.debug("reading Glue")

        t = tokens.next(level='querying')

        if isinstance(t, cls):
            return cls.from_another(t)

        tokens.push(t)
        return None

    @classmethod
    def _parse_glue_literal(cls, tokens):
        """
        Attempts to create a Glue from a literal.

        Returns the new Glue if it succeeds. Otherwise, returns None.
        (Doesn't back up to where it started; if we return
        None it's always a fatal error.)

        We're looking for a Dimen,
           - optionally followed by "plus <dimen>",
           - optionally followed by "minus <dimen>"
           - and in the plus/minus section, the units
             "fil+", i.e. "fi" plus any number of "l"s,
             are also allowed.
        """

        unit_cls = cls._dimen_units()
        new_fields = {}

        new_fields['space'] = Dimen.from_tokens(tokens,
                    unit_cls=unit_cls,
                    )

        tokens.eat_optional_spaces()

        if tokens.optional_string("plus"):
            new_fields['stretch'] = Dimen.from_tokens(tokens,
                    can_use_fil=True,
                    unit_cls=unit_cls,
                    )
            tokens.eat_optional_spaces()

        if tokens.optional_string("minus"):
            new_fields['shrink'] = Dimen.from_tokens(tokens,
                    can_use_fil=True,
                    unit_cls=unit_cls,
                    )
            tokens.eat_optional_spaces()

        return cls(**new_fields)

    def __repr__(self,
            show_unit = True,
            ):
        """
        Args:
            show_unit (bool): whether to show the units. This has no effect
                if a dimen is infinite: infinity units ("fil" etc)
                will always be displayed.
        """

        # Note an edge case: a Glue is fully initialised, with no
        # shrink or stretch, and a space which is a Dimen which is not
        # fully initialised. This will mean that the __repr__ of the Glue
        # is "Dimen; inchoate" which is confusing.

        try:
            result = self._space.__repr__(
                    show_unit=show_unit,
                    )

            if self._shrink.value or self._stretch.value:
                result += ' plus ' + self._stretch.__repr__(
                        show_unit=show_unit,
                        )

                if self._shrink.value:
                    result += ' minus ' + self._shrink.__repr__(
                            show_unit=show_unit,
                            )

            return result

        except AttributeError:
            return f'[{self.__class__.__name__}; inchoate]'

    @classmethod
    def _dimen_units(cls):
        return Dimen

    def __eq__(self, other):

        if not isinstance(other, self.__class__):
            return False

        return self._space==other._space and \
                self._stretch==other._stretch and \
                self._shrink==other._shrink

    def __int__(self):
        return int(self._space) # in sp

    @property
    def length(self):
        raise NotImplementedError()

    @property
    def width(self):
        # There was some code that thought the "size" property here was
        # called "width". This property exists to break that code.
        # Delete it when we're sure it's all gone.
        raise NotImplementedError()

    def __getstate__(self):
        """
        The value, in terms of simple types.

        This is always a list of one, three, or five elements:

            - [space] if shrink and stretch are zero;
            - [space, stretch, stretch_inf] if shrink is zero
                but stretch is not;
            - [space, stretch, stretch_inf, shrink, shrink_inf]
                if neither stretch nor shrink are zero.

        The infinity part of space is not included, since it's always zero.
        """

        # Just take the first part of the list, since self.space
        # must be finite.
        result = self.space.__getstate__(always_list=True)[:1]

        if self.shrink or self.stretch:
            result.extend(self.stretch.__getstate__(
                always_list=True))

            if self.shrink:
                result.extend(self.shrink.__getstate__(
                    always_list=True))

        logger.debug(
                "%s: __getstate__: returning %s",
                self, result)

        return result

    def __setstate__(self, state):

        if hasattr(self, '_value'):
            raise yex.exception.AlreadyInitialisedError()

        logger.debug(
                "%s %s: __setstate__: received %s",
                self.__class__.__name__, id(self), state)

        if not isinstance(state, list):
            raise TypeError()

        if len(state) not in (1, 3, 5):
            raise TypeError()

        if len(state)>3:
            logger.debug(
                    "%s %s: __setstate__: setting shrink: %s",
                    self.__class__.__name__, id(self),
                    state[3:5],
                    )
            self._shrink = Dimen.from_serial(state[3:5])
        else:
            self._shrink = Dimen()

        if len(state)>1:
            logger.debug(
                    "%s %s: __setstate__: setting stretch: %s",
                    self.__class__.__name__, id(self),
                    state[1:3],
                    )
            self._stretch = Dimen.from_serial(state[1:3])
        else:
            self._stretch = Dimen()

        logger.debug(
                "%s %s: __setstate__: setting space: %s",
                self.__class__.__name__, id(self),
                state[0:1], # this is correct; _space always has infinity=0
                )

        self._space = Dimen.from_serial([ state[0], 0 ])

        unit_cls = self._dimen_units()
        for thing in [self.space, self.stretch, self.shrink]:
            thing.unit_cls = unit_cls

        logger.debug(
                "%s %s: __setstate__: I'm back: %s",
                self.__class__.__name__, id(self), self,
                )
