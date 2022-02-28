import logging
import mex.exception

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')

class C_ControlWord:
    """
    Superclass of all control words.
    """

    is_deep = False

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

class C_Defined(C_ControlWord):
    pass
