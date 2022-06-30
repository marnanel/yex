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

def put_internal_after_other_internals(tokens, internal):
    """
    Puts an Internal token after all other Internal tokens at the front
        of the stream.

    Each Internal token at the start of the stream `tokens` is read but
    not executed. Then `internal` is pushed to the stream, and the other
    tokens are pushed back in reverse order.

    For example, if the front of the stream is `[a, b, c, X...]
    where `a`, `b`, and `c` are Internals and `X` is not,
    then after this function runs, the stream will contain
    `[a, b, c, internal, X...]` with no other changes.

    End of file is considered to be non-Internal for this purpose.

    If there are no Internal tokens at the start of the stream, we
    merely push `internal` and return.

    Args:
        tokens (`Expander`): the token stream
        internal (`Internal`): the Internal token to push

    Returns:
        `None`
    """

    import yex.parse

    found = []
    while True:
        found.append(tokens.next(
            level='deep',
            on_eof='none',
            ))
        if not isinstance(found[-1], yex.parse.Internal):
            break

    tokens.push(found.pop()) # works even if found[-1] is None

    tokens.push(internal)

    for t in reversed(found):
        tokens.push(t)
