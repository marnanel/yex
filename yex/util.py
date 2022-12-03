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

def fraction_to_str(x, p):
    r"""
    Decimal representation of x/2^p, to at most five decimal places.

    Based on prsc() by Don Knuth; with thanks to Gareth McCaughan.
    We use this routine rather than Python's own equivalent
    because this is how TeX does it, and they differ in places.

    There will always be at least one digit after the decimal point,
    even if the division is exact.

    Args:
        x (int): the numerator of the fraction you want to print
        p (int): log2 of the denominator of the fraction.
            (So for 123/65536 you would have x=123 and p=16)

    Returns:
        str
    """

    assert isinstance(x, int)
    assert isinstance(p, int)

    unity = 1<<p
    half = 1<<(p-1)
    s = ""
    if x<0: s,x = "-",-x
    s += str(x//unity)
    x = 10*(x&(unity-1)) + 5
    delta = 10
    s += "."
    while True:
        if delta > unity: x += half - (delta//2)
        s += chr(48+(x//unity)) # -- ord('0')==48
        x = 10*(x&(unity-1))
        delta *= 10
        if x <= delta: break
    return s
