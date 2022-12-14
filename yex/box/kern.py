from yex.box.gismo import Gismo
import logging

logger = logging.getLogger('yex.general')

class Kern(Gismo):
    """
    An adjustment of horizontal spacing.

    For example, a kern would appear between the capital letters "A" and "V".
    """

    discardable = True

    def __init__(self, width):
        super().__init__(
                width = width,
                )

    def __repr__(self):
        return f'[kern: {self.width}]'

    def showbox(self):
        return [r'\kern' +
                self.width.__repr__(show_unit=False)]

    def __getstate__(self):
        return {
                'kern': self.width.value,
                }

    @property
    def symbol(self):
        return '∿'
