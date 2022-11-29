import os

class _ShowCaller:
    """
    Singleton class whose representation names the caller of the caller.

    The object of this class does nothing in particular most of the time.
    But when you use it in the parameters of a logging statement, thus:

    ```
        logger.debug("ready; was called from %s", show_caller)
    ```

    it returns a string giving the name, filename, and line number
    of the caller of the method containing the logging statement.

    If this was done using a function call, the call would take place
    every time the logging statement was executed, even in production
    where it would be a no-op.

    Attributes:
        DEPTH (`int`): how many levels of directory we should consider
            to be part of our package, rather than being library modules.
    """

    DEPTH = 1

    def __init__(self):
        self.prefix = os.path.sep.join(
                __file__.split(os.path.sep)[:-self.DEPTH]
        )

    def __repr__(self):
        import traceback

        stack = reversed(list(enumerate(traceback.extract_stack()[:-1])))

        for i, caller in stack:
            if caller.filename.startswith(self.prefix):
                break

        try:
            i, caller = next(stack)
            return '%s (%s:%s)' % (
                    caller.name,
                    caller.filename[len(self.prefix)+1:],
                    caller.lineno,
                    )
        except StopIteration:
            return '???'

show_caller = _ShowCaller()

def only_ascii(c):
    if c>=' ' and c<='~':
        return c
    else:
        return '(%02x)' % (ord(c),)

def unless_inherit(s):
    if s=='inherit':
        return 0
    else:
        return s
