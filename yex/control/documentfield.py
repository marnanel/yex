from yex.control.parameter import Parameter
import yex.font
import logging

logger = logging.getLogger('yex.general')

class DocumentField(Parameter):
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
