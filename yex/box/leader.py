import yex
from yex.box.gismo import Gismo
import logging

logger = logging.getLogger('yex.general')

class Leader(Gismo):
    """
    Leaders, although at present this only wraps Glue.

    Attributes:
        glue (`Glue`): the glue we're wrapping.
           If the constructor is given glue=None,
           we construct a new Glue using **kwargs
           and wrap that, instead. If it's str, we look up the param
           with the given name and use Glue of that length; in this
           case, you must also provide `doc` to the constructor.

        vertical (`bool`): True if this Leader is vertical,
            False (which is the default) if it's horizontal.

        name (str or None): the name to be displayed in showbox.
            If you leave this as None, no glue will be supplied;
            however, if name is None and glue is a str, name
            will be taken from that str.

        length (Dimen or None): the length of this box (which is
            the width if we're horizontal, and the height if we're
            vertical), overriding the glue. This is None unless
            we've been through wrapping.
    """

    discardable = True

    def __init__(self,
            glue=None,
            vertical=False,
            doc=None,
            name=None,
            ch=' ',
            **kwargs,
            ):
        """
        Constructor.

        """
        self.name = None
        self.length = None
        self.vertical = vertical
        self.ch = ch

        if glue is None:
            self.glue = yex.value.Glue(**kwargs)
        elif isinstance(glue, yex.value.Glue):
            self.glue = glue
        elif isinstance(glue, str):
            assert doc is not None

            self.glue = doc.get(glue, param_control=False)
            self.name = glue
        else:
            raise TypeError(glue)

        for name in [
                'space', 'stretch', 'shrink',
                ]:
            setattr(self, name, getattr(self.glue, name))

    @classmethod
    def from_another(cls, another):
        result = cls.__new__(cls)
        result.vertical = another.vertical
        result.ch = another.ch

        if another.glue is None:
            result.glue = None
        else:
            result.glue = yex.value.Glue.from_another(another.glue)

        return result

    @property
    def contents(self):
        return []

    @property
    def width(self):
        if self.vertical:
            return yex.value.Dimen(0)
        elif self.length is not None:
            return self.length
        else:
            return self.glue.space

    @property
    def height(self):
        if not self.vertical:
            return yex.value.Dimen(0)
        elif self.length is not None:
            return self.length
        else:
            return self.glue.space

    @property
    def depth(self):
        return yex.value.Dimen(0)

    def __repr__(self):
        result = '[' + repr(self.glue)
        if self.name:
            result += f' ({self.name})'
        if self.vertical:
            result += ';vertical'
        if self.length is not None:
            result += f';length={self.length}'
        result += ']'
        return result

    def showbox(self):
        result = r'\glue'
        if self.name:
            result += fr'({self.name})'
        result += ' ' + self.glue.__repr__(show_unit=False)
        return [result]

    def __eq__(self, other):
        if isinstance(other, yex.value.Glue):
            return self.glue==other
        else:
            try:
                return self.vertical==other.vertical and \
                        self.glue==other.glue
            except AttributeError:
                return False

    def __getstate__(self):
        r"""
        The value, in terms of simple types.

        If self.ch isn't a single space, which is its usual value,
        we return a dict:
            * "ch": self.ch
            * "leader": self.glue

        If self.ch is a single space:

        since Leaders occur all over the place in the final output,
        where they're almost always finite with no stretch or shrink,
        we represent that as a special case:
        just the integer size of the space.

        Otherwise, this is the same as the __getstate__() of the glue.
        """

        result = self.glue.__getstate__()

        if self.ch!=' ':
            result = {
                    'leader': result,
                    'ch': self.ch,
                    }
        elif len(result)==1:
            result = result[0]

        return result

    @property
    def symbol(self):
        return '︙'
