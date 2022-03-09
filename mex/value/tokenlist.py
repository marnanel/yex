import string
import mex.exception
import mex.parse
import logging
from mex.value.value import Value

commands_logger = logging.getLogger('mex.commands')

class Tokenlist(Value):
    def __init__(self,
            tokens = None):

        super().__init__(tokens)

        if tokens is None:
            self.value = []
        elif isinstance(tokens, list):
            self.tokens = None
            self.value = []
        elif isinstance(tokens, (Tokenlist, mex.parse.Tokeniser)):
            self.set_from_tokens(tokens)
        else:
            self.value = [
                    mex.parse.Token(c)
                    for c in str(tokens)
                    ]

        self._iterator = self._read()

    def set_from_tokens(self, tokens):

        for t in tokens:
            break

        if t.category!=t.BEGINNING_GROUP:
            raise mex.exception.ParseError("expected a token list")

        tokens.push(t)

        e = mex.parse.Expander(tokens,
                running=False,
                single=True,
                )

        self.value = list(e)

        commands_logger.debug("%s: set value from tokens = %s",
                self,
                self.value)

    def __iter__(self):

        read = self._read

        class Tokenlist_iterator:
            def __init__(self):
                self.iterator = read()

            def __next__(self):
                return self.iterator.__next__()

        return Tokenlist_iterator()

    def __next__(self):
        return self._iterator.__next__()

    def _read(self):
        for token in self.value:
            commands_logger.debug("%s: yield member %s",
                    self, token)
            yield token
        commands_logger.debug("%s: all done",
                self)

    def __eq__(self, other):
        if isinstance(other, Tokenlist):
            return self.value==other.value
        elif isinstance(other, list):

            return self.value == other

        elif isinstance(other, str):
            return self.value==[
                    mex.parse.Token(ch=c)
                    for c in other]
        else:
            raise TypeError(
                    f"{self} can't be compared "
                    f"with {other}, which is {other.__class__}"
                    )

    def __repr__(self):
        return f'[token list %x: %d: %s]' % (
                id(self)%0xFFFF,
                len(self.value),
                str(self),
                )

    def __str__(self):
        return ''.join([x.ch for x in self.value])

    def __len__(self):
        return len(self.value)

    def __bool__(self):
        return len(self.value)!=0

    def __getitem__(self, index):
        return self.value[index]

    def __setitem__(self, index, v):
        self.value[index] = v
