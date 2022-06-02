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
            t = None,
            space = 0.0,
            space_unit = None,
            stretch = 0.0,
            stretch_unit = None,
            shrink = 0.0,
            shrink_unit = None,
            ):

        """
        t can be a Tokeniser,
            in which case we attempt to parse a Glue from it.
        Or it can be numeric,
            in which case it overrides "space".
        Or it can be None.

        space, stretch, and shrink are all numeric. They're passed to
        Dimen()'s constructor along with the unit supplied.

        space_unit, stretch_unit, and shrink_unit are the units for
        the space, stretch, and shrink parameters, respectively.
        In addition to the usual possibilities,
        stretch_unit and shrink_unit may be 'fi', 'fii', or 'fiii'
        for infinities.
        """

        if t is not None:
            if isinstance(t, yex.parse.Tokenstream):
                self._parse_glue(t)
                return
            else:
                space = t

        self._space = Dimen(space,
                unit=space_unit)
        self._stretch = Dimen(stretch,
                unit=stretch_unit,
                can_use_fil=True,
                )
        self._shrink = Dimen(shrink,
                unit=shrink_unit,
                can_use_fil=True,
                )

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
            # valid Glue at all, so call self._raise_parse_error()

            logger.debug("reading Glue; not a variable")
            return False

        value = control.value

        if not isinstance(value, Glue):
            logger.debug(
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
        result = f"{float(self._space)}"

        if self.shrink.value:
            result += (
                    f" plus {float(self._stretch)} "
                    f" minus {float(self._shrink)}"
                    )
        elif self.stretch.value:
            result += f" plus {float(self._stretch)}"

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

        form = '%(space)s'

        if self.shrink.value or self.stretch.value:
            form += ' plus %(stretch)s'

            if self.shrink.value:
                form += ' minus %(shrink)s'

        values = dict([
            (f, v.__repr__(show_unit)) for f,v in [
                ('space', self._space),
                ('shrink', self._shrink),
                ('stretch', self._stretch),
                ]])

        result = form % values

        return result

    def _dimen_units(self):
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
