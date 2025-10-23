from yex.box.gismo import Gismo
import yex.logging

logger = yex.logging.getLogger('box')

class Kern(Gismo):
    r"""
    An adjustment of horizontal spacing. Generally, this is a box
    with negative width.

    For example, a kern would appear between the capital letters "A" and "V".

    Attributes:
        width: the width of the kern. Mostly this is negative.
        explicit: if True, this kern was created using `\kern`
            or similar. If False, the kern was requested by a font.
    """

    discardable = True

    def __init__(self,
                 width: Dimen,
                 explicit: bool = False,
            ):
        super().__init__(
                width = width,
                )
        self.explicit = explicit

    def __repr__(self):
        if self.explicit:
            explicit = ' (explicit)'
        else:
            explicit = ''

        return f'[kern:{self.width}{explicit}]'

    def showbox(self):
        if self.explicit:
            space = ' '
        else:
            space = ''

        # We add a space between the word "\kern" and the distance if the
        # kern is explicit. This is weird, but it's how TeX does it.
        #
        # LuaTeX, by contrast, never includes a space and adds " (font)"
        # if the kern is implicit.

        return [r'\kern' + space +
                self.width.__repr__(show_unit=False)]

    def __getstate__(self):
        result = {
                'kern': self.width.value,
                }

        if self.explicit:
            result['explicit'] = True

        return result

    @property
    def symbol(self):
        return '∿'
