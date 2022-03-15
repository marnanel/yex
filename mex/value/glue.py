import string
import mex.exception
import mex.parse
import logging
from mex.value.value import Value
from mex.value.dimen import Dimen

commands_logger = logging.getLogger('mex.commands')

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

        self.width = Dimen()

        if t is not None:
            if isinstance(t, mex.parse.Tokenstream):
                self.tokens = t
                self._parse_glue()
                return
            else:
                space = t

        self.tokens = None
        self.space = Dimen(space,
                unit=unit)
        self.stretch = Dimen(stretch,
                infinity = stretch_infinity,
                unit=unit)
        self.shrink = Dimen(shrink,
                infinity = shrink_infinity,
                unit=unit)
        self.width.value = self.space.value

    def _raise_parse_error(self):
        """
        I'm sorry, I haven't a Glue
        """
        raise mex.exception.MexError(
                "Expected a Glue")

    def _parse_glue(self):

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

            if handler(self.tokens):
                return

        self._raise_parse_error()

    def _parse_glue_variable(self, tokens):
        """
        Attempts to initialise this object from
        a variable containing a Glue.

        Returns True if it succeeds. Otherwise, backs up to where
        it started and returns False.
        """

        is_negative = self.optional_negative_signs()

        commands_logger.debug("reading Glue; is_negative=%s",
                is_negative)

        for t in self.tokens:
            break

        if not t.category==t.CONTROL:
            # this is not a Glue variable; rewind
            self.tokens.push(t)
            # XXX If there were +/- symbols, this can't be a
            # valid Glue, so call self._raise_parse_error()

            commands_logger.debug("reading Glue; not a variable")
            return False

        control = self.tokens.state.get(
                field = t.name,
                tokens = self.tokens,
                )

        value = control.value

        if not isinstance(value, Glue):
            commands_logger.debug(
                    "reading Glue; %s==%s, which is not a control but a %s",
                    control, value, type(value))
            self._raise_parse_error()

        self.space = value.space
        self.stretch = value.stretch
        self.shrink = value.shrink

        self.width.value = self.space.value

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

        self.space = Dimen(tokens,
                    unit_obj=unit_obj,
                    )
        self.width.value = self.space.value

        tokens.eat_optional_spaces()

        if tokens.optional_string("plus"):
            self.stretch = Dimen(tokens,
                    can_use_fil=True,
                    unit_obj=unit_obj,
                    )
            tokens.eat_optional_spaces()
        else:
            self.stretch = Dimen(0)

        if tokens.optional_string("minus"):
            self.shrink = Dimen(tokens,
                    can_use_fil=True,
                    unit_obj=unit_obj,
                    )
            tokens.eat_optional_spaces()
        else:
            self.shrink = Dimen(0)

        return True

    def __repr__(self):
        result = f"{self.space}"

        if self.shrink.value:
            result += f" plus {self.stretch} minus {self.shrink}"
        elif self.stretch.value:
            result += f" plus {self.stretch}"

        return result

    def _dimen_units(self):
        return None # use the default units for Dimens

    def __eq__(self, other):
        return self.space==other.space and \
                self.stretch==other.stretch and \
                self.shrink==other.shrink

    def __int__(self):
        return int(self.space) # in sp

    def showbox(self):
        return []
