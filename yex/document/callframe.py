import logging

logger = logging.getLogger('yex.general')

class Callframe:
    """
    Description of a macro call.

    Only used for tracebacks; the macros take care of themselves.
    Stored in the list Document.call_stack.

    Attributes:
        callee (`Token`): the name of the macro that made the call.
        args (list of lists of `Token`): the arguments to the call.
        location (`yex.parse.Location`): where the call was made
            (as a named tuple of filename, line, and column).
    """
    def __init__(self,
            callee,
            args,
            location,
            ):
        self.callee = callee
        self.args = args
        self.location = location

    def __repr__(self):
        args = ','.join([
            ''.join([str(c) for c in v])
            for (f,v) in sorted(self.args.items())])
        return f'{self.callee}({args}):{self.location}'

    def jump_back(self, tokens):
        logger.debug("%s: jumping back", self)
        tokens.location = self.location
