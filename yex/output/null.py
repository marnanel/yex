import logging
import yex
from yex.output.output import Output

logger = logging.getLogger('yex.general')

class Null(Output):
    """
    An output driver that does nothing but complain if you talk to it.

    And honestly, don't we all have days like that?

    Output.driver_for() returns a Null instance if you pass it
    filename==None.
    """

    def __init__(self,
            doc,
            filename):

        super().__init__(doc=doc, filename=filename)

        logger.debug('Null output: created, for filename==%s', filename)

    @classmethod
    def can_handle(cls, file_extension):
        return False

    def render(self):
        if not self.doc.contents:
            return # fair enough

        raise yex.exception.NoOutputDriverError() # except us, obviously
