import string
import yex.exception
import yex.parse
import logging
import copy
from yex.value.value import Value

logger = logging.getLogger('yex.general')

class Tokenlist(Value):
    """
    A sequence of Tokens.

    Attributes:
        value (list): the Tokens we represent. Only instances of
            yex.parse.Token are allowed here.
    """

    def __init__(self,
            value = None):

        super().__init__()

        if value is None:
            self.value = []
            return
        elif not isinstance(value, list):
            value = [
                    yex.parse.get_token(
                        ch = c,
                        )
                    for c in str(value)
                    ]

        not_tokens = [x for x in value
                if not isinstance(x, yex.parse.Token)]

        if not_tokens:
            raise yex.exception.YexError(
                    "Expected a list of Tokens, but it contained "
                    f"{not_tokens}"
                    )

        self.value = value

    @classmethod
    def from_tokens(cls, tokens,
            require_open_bracket = False,
            ):

        if require_open_bracket:
            t = tokens.next(level='deep')

            if t.category!=t.BEGINNING_GROUP:
                raise yex.exception.ParseError(
                        "expected a token list "
                        f"but found {t}"
                        )
            tokens.push(t)

        logger.debug("constructing new Tokenlist from %s",
                tokens)

        value = list(
                tokens.single_shot(
                    level = 'deep',
                    ))

        logger.debug("so, initial value is: %s",
                value)

        result = cls(value)
        return result

    @classmethod
    def from_another(cls, other):
        logger.debug("constructing new Tokenlist from %s",
                other)

        return cls(value=list(other.value))

    def __iter__(self):

        read = self._read

        class Tokenlist_iterator:
            def __init__(self):
                self.iterator = read()

            def __next__(self):
                return self.iterator.__next__()

        return Tokenlist_iterator()

    def _read(self):
        for token in self.value:
            logger.debug("%s: yield member %s",
                    self, token)
            yield token
        logger.debug("%s: all done",
                self)

    def __eq__(self, other):
        if isinstance(other,
                (Tokenlist, yex.parse.Tokenstream)):

            return self.value==other.value
        elif isinstance(other, list):

            return self.value == other

        elif isinstance(other, str):
            return self.value==[
                    yex.parse.get_token(ch=c)
                    for c in other]
        else:
            raise TypeError(
                    f"{self} can't be compared "
                    f"with {other}, which is {other.__class__}"
                    )

    def __repr__(self):
        return f'[token list %x: %s]' % (
                id(self)%0xFFFF,
                str(self),
                )

    def __str__(self):
        return ''.join([str(x) for x in self.value])

    def __len__(self):
        return len(self.value)

    def __bool__(self):
        return len(self.value)!=0

    def __getitem__(self, index):
        return self.value[index]

    def __setitem__(self, index, v):
        self.value[index] = v

    def __deepcopy__(self, memo):
        contents = [
                copy.deepcopy(v)
                for v in self.value
                ]
        result = Tokenlist(contents)
        return result

    @property
    def name(self):
        return self.__class__.__name__

    def push_to(self, tokens):
        """
        Pushes the contents of this Tokenlist onto an Expander.

        Args:
            tokens (`Expander`): where to push it
        """
        for t in reversed(self.value):
            tokens.push(t)
