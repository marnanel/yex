import string
import yex.exception
import yex.parse
import logging
from yex.value.value import Value
from yex.value.dimen import Dimen

commands_logger = logging.getLogger('yex.commands')

class Glue(Value):
    """
    A space between the smaller Boxes inside a Box.

    A Glue has space, stretch, and shrink.

    The specifications for Glue may be found in ch12
    of the TeXbook, beginning on page 69.
    """

    def __init__(self,
            t = None,
            unit = None,
            space = 0.0,
            stretch = 0.0,
            shrink = 0.0,
            stretch_infinity = 0,
            shrink_infinity = 0,
            ):

        """
        t can be a Tokeniser,
            in which case we attempt to parse a Glue from it.
        Or it can be numeric,
            in which case it overrides "space".
        Or it can be None.

        space, stretch, and shrink are all numeric. They're passed to
        Dimen()'s constructor along with the unit supplied.

        stretch_infinity and shrink_infinity are integers
        which will be supplied to Dimen's constructor along
        with stretch and shrink.
        """

        if t is not None:
            if isinstance(t, yex.parse.Tokenstream):
                self._parse_glue(t)
                self.length = Dimen(self.space)
                return
            else:
                space = t

        self.length = Dimen(space,
                unit=unit)
        self._space = Dimen(space,
                unit=unit)
        self._stretch = Dimen(stretch,
                infinity = stretch_infinity,
                unit=unit)
        self._shrink = Dimen(shrink,
                infinity = shrink_infinity,
                unit=unit)

    @property
    def space(self):
        return self._space
    @property
    def stretch(self):
        return self._stretch
    @property
    def shrink(self):
        return self._shrink

    def _raise_parse_error(self):
        """
        I'm sorry, I haven't a Glue
        """
        raise yex.exception.YexError(
                "Expected a Glue")

    def _parse_glue(self, tokens):

        # We're either looking for
        #    optional_negative_signs and then one of
        #       * glue parameter
        #       * \lastskip
        #       * a token defined with \skipdef
        #       * \skipNNN register
        # Or
        #    Dimen,
        #       optionally followed by "plus <dimen>",
        #       optionally followed by "minus <dimen>"
        #    and in the plus/minus section, the units
        #     "fil+", i.e. "fi" plus any number of "l"s,
        #     are also allowed.

        for handler in [
                self._parse_glue_variable,
                self._parse_glue_literal,
                ]:

            if handler(tokens):
                return

        self._raise_parse_error()

    def _parse_glue_variable(self, tokens):
        """
        Attempts to initialise this object from
        a variable containing a Glue.

        Returns True if it succeeds. Otherwise, backs up to where
        it started and returns False.
        """

        is_negative = self.optional_negative_signs(tokens)

        commands_logger.debug("reading Glue; is_negative=%s",
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
            # valid Glue at all, so call self._raise_parse_error()

            commands_logger.debug("reading Glue; not a variable")
            return False

        value = control.value

        if not isinstance(value, Glue):
            commands_logger.debug(
                    "reading Glue; %s==%s, which is not a control but a %s",
                    control, value, type(value))
            self._raise_parse_error()

        self._space = value.space
        self._stretch = value.stretch
        self._shrink = value.shrink

        return True

    def _parse_glue_literal(self, tokens):
        """
        Attempts to initialise this object from
        a literal representing a Glue.

        Returns True if it succeeds. Otherwise, returns False.
        (Doesn't back up to where it started; if we return
        False it's always a fatal error.)

        Note: At present we always return True. If this isn't a
        real Glue literal it'll fail on attempting to read
        the first Dimen.
        """

        unit_obj = self._dimen_units()

        self._space = Dimen(tokens,
                    unit_obj=unit_obj,
                    )

        tokens.eat_optional_spaces()

        if tokens.optional_string("plus"):
            self._stretch = Dimen(tokens,
                    can_use_fil=True,
                    unit_obj=unit_obj,
                    )
            tokens.eat_optional_spaces()
        else:
            self._stretch = Dimen(0)

        if tokens.optional_string("minus"):
            self._shrink = Dimen(tokens,
                    can_use_fil=True,
                    unit_obj=unit_obj,
                    )
            tokens.eat_optional_spaces()
        else:
            self._shrink = Dimen(0)

        return True

    def __repr__(self):
        result = f"{self._space}"

        if self.shrink.value:
            result += f" plus {self._stretch} minus {self._shrink}"
        elif self.stretch.value:
            result += f" plus {self._stretch}"

        if self.length != self._space:
            result += f" now {self.length}"

        return result

    def _dimen_units(self):
        return None # use the default units for Dimens

    def __eq__(self, other):

        if not isinstance(other, Glue):
            return False

        return self.length==other.length and \
                self._stretch==other._stretch and \
                self._shrink==other._shrink

    def __int__(self):
        return int(self.length) # in sp

    def showbox(self):
        return []

    @property
    def width(self):
        # There was some code that thought the "size" property here was
        # called "width". This property exists to break that code.
        # Delete it when we're sure it's all gone.
        raise NotImplementedError()
