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
            stretch = 0.0,
            stretch_unit = None,
            shrink = 0.0,
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
                    raise yex.exception.YexError(
                            f'"{arg}" was a Dimen, '
                            f'but {arg}_unit was not None'
                            )

                if not can_be_infinite and length.infinity!=0:
                    raise yex.exception.YexError(
                            f'"{arg}" must be finite'
                            )
                return Dimen.from_another(length)
            else:
                try:
                    length = float(length)
                except TypeError:
                    raise yex.exception.YexError(
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
        raise yex.exception.YexError(
                "Expected a Glue")

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

        We're looking for optional_negative_signs, and then one of
           - glue parameter
           - \lastskip
           - a token defined with \skipdef
           - a \skipNNN register

        Returns True if it succeeds. Otherwise, backs up to where
        it started and returns False.
        """

        is_negative = cls.optional_negative_signs(tokens)

        new_fields = {}

        logger.debug("reading Glue; is_negative=%s",
                is_negative)

        t = tokens.next()

        if isinstance(t, (
            yex.control.C_Control,
            yex.register.Register,
            )):
            control = t

        elif isinstance(t, yex.parse.Control):
            control = tokens.doc.get(
                    field = t.identifier,
                    tokens = tokens,
                    )
        else:
            # this is not a Glue variable; rewind
            tokens.push(t)
            # XXX If there were +/- symbols, this can't be a
            # valid Glue at all, so call cls._raise_parse_error()

            logger.debug("reading Glue; not a variable")
            return None

        value = control.value

        if not isinstance(value, Glue):
            logger.debug(
                    "reading Glue; %s==%s, which is not a control but a %s",
                    control, value, type(value))
            cls._raise_parse_error()

        return cls.from_another(value)

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

        result = cls(**new_fields)
        logger.debug(
                'parsed Glue: %s -> %s',
                new_fields, result)
        return result

    def __repr__(self,
            show_unit = True,
            ):
        """
        Args:
            show_unit (bool): whether to show the units. This has no effect
                if a dimen is infinite: infinity units ("fil" etc)
                will always be displayed.
        """

        try:
            form = '%(space)s'

            if self._shrink.value or self._stretch.value:
                form += ' plus %(stretch)s'

                if self._shrink.value:
                    form += ' minus %(shrink)s'

            values = dict([
                (f, v.__repr__(show_unit)) for f,v in [
                    ('space', self._space),
                    ('shrink', self._shrink),
                    ('stretch', self._stretch),
                    ]])

            result = form % values

            return result
        except AttributeError:
            return f'[{self.__class__.__name__}; inchoate]'

    @classmethod
    def _dimen_units(cls):
        return None # use the default units for Dimens

    def __eq__(self, other):

        if not isinstance(other, Glue):
            return False

        return self._space==other._space and \
                self._stretch==other._stretch and \
                self._shrink==other._shrink

    def __int__(self):
        return int(self._space) # in sp

    def showbox(self):
        return []

    @property
    def length(self):
        raise NotImplementedError()

    @property
    def width(self):
        # There was some code that thought the "size" property here was
        # called "width". This property exists to break that code.
        # Delete it when we're sure it's all gone.
        raise NotImplementedError()
