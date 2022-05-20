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
            t = None):

        super().__init__()

        if t is None:
            self.value = []
        elif isinstance(t, list):

            not_tokens = [x for x in t
                    if not isinstance(x, yex.parse.Token)]

            if not_tokens:
                raise yex.exception.YexError(
                        "Expected a list of Tokens, but it contained "
                        f"{not_tokens}"
                        )

            self.value = t

        elif isinstance(t, yex.parse.Expander):

            self.value = []
            for thing in t.another(
                    single = True,
                    level = 'deep',
                    on_eof = 'exhaust',
                    ):
                logger.debug("%s: adding value: %s",
                        self, thing)

                self.value.append(thing)

            logger.debug("%s: so, initial value is: %s",
                    self, self.value)

        elif isinstance(t, Tokenlist):
            self.value = copy.copy(t.value)
        else:
            self.value = [
                    yex.parse.get_token(
                        ch = c,
                        )
                    for c in str(t)
                    ]

    def set_from_tokens(self, tokens):

        t = tokens.next(level='deep')

        if t.category!=t.BEGINNING_GROUP:
            raise yex.exception.ParseError(
                    "expected a token list "
                    f"but found {t}"
                    )

        tokens.push(t)

        self.value = list(
                tokens.single_shot(
                    level = 'reading',
                    ))

        logger.debug("%s: set value from tokens = %s",
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
