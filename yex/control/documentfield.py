from yex.control.parameter import C_Parameter
import yex.font
import logging

logger = logging.getLogger('yex.general')

class C_DocumentField(C_Parameter):
    """
    A reference to a field in a Document instance.

    This allows doc[...] to access the field using subscripting like
    any other control, rather than having to special-case it.
    """

    do_not_initialise = True

    @property
    def fieldname(self):
        r"""
        The name of the field in Document we represent.

        Not our own name in the controls table: there should be no
        leading underscore.
        """
        return self.__class__.__name__[3:]

    def _get_value(self):
        try:
            return getattr(self.doc, self.fieldname)
        except AttributeError as ae:
            raise yex.exception.CannotGetError(
                    field = self.fieldname,
                    problem = ae,
                    )

    def _set_value(self, value):
        try:
            setattr(self.doc, self.fieldname, value)
        except AttributeError as ae:
            raise yex.exception.CannotSetError(
                    field = self.fieldname,
                    value = value,
                    problem = ae,
                    )

    def __getstate__(self):
        # don't bother with wrapping it in a dict saying the name of
        # the control; we're looking at the document itself here,
        # and these names can't be overridden
        return self._get_value()

class X__mode(C_DocumentField):

    our_type = (yex.mode.Mode, str)

    def _get_value(self):
        if self.doc.mode is None:
            self.doc.mode = yex.mode.Vertical(doc=self.doc)
            logger.debug(
                    "created Mode on first request: %s",
                    self.doc.mode)

        return super()._get_value()

    def _set_value(self, value):

        if not hasattr(value, 'append'):
            # okay, maybe it's the name of a mode
            try:
                handler = yex.mode.Mode.handlers[str(value)]
            except KeyError:
                raise ValueError(f"no such mode: {value}")

            value = handler(self.doc)

        super()._set_value(value)

class X__modelist(C_DocumentField):

    our_type = list

    def _get_value(self):
        if self.doc.mode is None:
            self.doc['_mode']

        return self.doc.mode.list

    def _set_value(self, value):
        if self.doc.mode is None:
            self.doc['_mode']

        self.doc.mode.list = value

class X__font(C_DocumentField):

    our_type = (yex.font.Font, str)

    def _get_value(self):
        if not hasattr(self, 'doc'):
            raise ValueError()
        if self.doc.font is None:
            self.doc.font = yex.font.Font.from_name(
                    name=None,
                    doc=self,
                    )
            logger.debug(
                    "created Font on first request: %s",
                    self.doc.font)

        return super()._get_value()

    def _set_value(self, value):
        if isinstance(value, str):
            value = yex.font.get_font_from_name(
                    name=value,
                    doc=self.doc,
                    )
        elif not isinstance(value, yex.font.Font):
            raise TypeError(f'{value} is not a Font but a {type(value)}')

        super()._set_value(value)

class X__fonts(C_DocumentField):
    our_type = dict

class X__parshape(C_DocumentField):
    our_type = list

class X__next_assignment_is_global(C_DocumentField):
    our_type = bool

class X__output(C_DocumentField):
    our_type = yex.output.Output

class X__created(C_DocumentField):
    our_type = int

class X__contents(C_DocumentField):
    our_type = list
