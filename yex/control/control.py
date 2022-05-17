import logging
import yex.exception

logger = logging.getLogger('yex.general')

class C_Control:
    """
    Superclass of all controls.

    A control has:
       - a name, which is a string. If you don't pass one in,
            we default to the name of the class in lowercase.
       - a __call__() method, which causes it to run
       - the flags is_long and is_outer, which affect
            where it can be called

    Each control is usually referred to by at least one
    yex.parse.Control object in a given Document. But those objects
    are symbols, and these are procedures; don't get them confused.

    A Document keeps track of many controls. The control
    doesn't know which doc it's in, but when it's called, it
    can find it by looking in the `doc` field of `tokens`.

    Some controls (such as the superclass) have names
    beginning with `C_`. This is so that they can't be called
    from TeX code; TeX identifiers can't contain underscores.
    If they began with a plain underscore, Python wouldn't export
    them from their modules.
    """

    def __init__(self,
            is_long = False,
            is_outer = False,
            name = None,
            *args, **kwargs):

        self.is_long = is_long
        self.is_outer = is_outer

        if name is None:
            self.name = self.__class__.__name__.lower()
        else:
            self.name = name

    @property
    def identifier(self):
        """
        A good string to use for looking up this control in a document.

        In practice, it could be stored under a different string as well,
        or instead, or it might not be stored at all. But this is often
        a reasonable shot.
        """
        return fr'\{self.name}'

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    def __repr__(self):
        return fr'[\{self.name}]'

class C_Expandable(C_Control):
    """
    Superclass of all expandable controls.

    Expandable controls include all macros, and
    some control flow primitives.

    For full details, see the TeXbook, p211f.
    """
    def __call__(self, tokens):
        raise NotImplementedError()

class C_Unexpandable(C_Control):
    """
    Superclass of all unexpandable controls.

    Unexpandable controls are the most basic primitives.
    All of them carry flags saying which modes they can
    run in. True means the control is permitted;
    False means it's forbidden; a string which is the name of a mode
    forces a switch to that mode before it's used.

    For full details, see the TeXbook, p211f.
    """

    vertical = True
    horizontal = True
    math = True

    def __call__(self, tokens):
        raise NotImplementedError()

class C_Not_for_calling(C_Unexpandable):
    """
    There are a few controls which shouldn't be called.
    Mostly this is because they're only designed to be subscripted.
    """
    def __getitem__(self, n):
        return NotImplementedError()

    def __call__(self, tokens):
        raise ValueError("Not for calling")
