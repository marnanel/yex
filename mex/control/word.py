import logging
import mex.exception

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')

class C_ControlWord:
    """
    Superclass of all control words.

    A control word has:
       - a name, which is a string. If you don't pass one in,
            we default to the name of the class in lowercase.
       - a __call__() method, which causes it to run
       - the flags is_long and is_outer, which affect
            where it can be called

    Each C_ControlWords is usually referred to by at least one
    mex.parse.Control object in a given State. But those objects
    are symbols, and these are procedures; don't get them confused.

    A State keeps track of many C_ControlWords. The C_ControlWord
    doesn't know which state it's in, but when it's called, it
    can find it with "tokens.state".

    Some C_ControlWords (such as the superclass) have names
    beginning with "C_". This is so that they can't be called
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

    def __call__(self, name, tokens):
        raise NotImplementedError()

    def __repr__(self):
        return f'[\\{self.name}]'

class C_Expandable(C_ControlWord):
    """
    Superclass of all expandable control words.

    Expandable control words include all macros, and
    some control flow primitives.

    For full details, see the TeXbook, p211f.
    """
    pass

class C_Unexpandable(C_ControlWord):
    """
    Superclass of all unexpandable control words.

    Unexpandable control words are the most basic primitives.

    For full details, see the TeXbook, p211f.
    """
    pass

class C_Defined(C_Expandable):
    pass
