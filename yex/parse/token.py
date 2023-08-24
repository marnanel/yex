import yex.exception
import logging

logger = logging.getLogger('yex.general')

class Token:
    r"""
    A categorised symbol.

    The tokeniser runs through the files it reads, categorising each character
    into one of these groups. It uses a lookup table in
    `yex.control.keyword.Catcode` for this. You can find the default values
    over there.

    A few groups are never used outside the tokeniser; the rest have
    subclasses within this module.

    Attributes:
        category (int between 0 and 15, or any character from "cip"): the
            category of this Token. Symbolic constants for these categories
            are given at the start of this class. Categories represented
            by integers are as used in TeX; those represented by characters
            are internal to yex, and should not be seen by the end user.

            Categories are chosen when the Token is created: there's no
            necessary connection between character and category. But
            each possible character has a default category, assigned in
            the Catcode table. These defaults can change during a run.
            The state of these defaults at the beginning of a run
            depends on whether you're using plain.tex.

        ch (str of length 1, with codepoint between 0 and 126 inclusive):
            the character represented by this Token.

        location (Location, or None): where we found the character
            which we turned into this Token. Used for error messages.

    Specification of the serialisation format:

    A Token is represented by a (category, ch) tuple. A similar two-item
    list works just as well.

    When sequences of tokens are serialised together, they are produced
    in a list. Any Tokens in that list whose category was SPACE, LETTER,
    or OTHER, and whose ch would have produced that category at the start
    of the run, is turned into the corresponding character. Strings of these
    characters are concatenated.

    Note that "at the start of the run" is not the default categories
    you get if you initialise a Token() with no category parameter.
    This is to mimic TeX's behaviour.
    """

    ESCAPE = 0
    BEGINNING_GROUP = 1
    END_GROUP = 2
    MATH_SHIFT = 3
    ALIGNMENT_TAB = 4
    END_OF_LINE = 5
    PARAMETER = 6
    SUPERSCRIPT = 7
    SUBSCRIPT = 8
    IGNORED = 9
    SPACE = 10
    LETTER = 11
    OTHER = 12
    ACTIVE = 13
    COMMENT = 14
    INVALID = 15

    CONTROL = 'c'
    INTERNAL = 'i'
    PARAGRAPH = 'p'
    ARGUMENT = 'a'

    # This will be set further down the file, when the subclasses
    # have been defined.
    by_category = None

    DISAPPEARS_AFTER_CONTROL = (SPACE, END_OF_LINE)

    def __init__(self,
            ch,
            location = None):

        if type(self)==Token:
            raise yex.exception.ConstructorError()

        self.ch = ch
        self.location = location

    @property
    def category(self):
        """
        The category number, as given on p37 of the TeXbook.
        """
        return self._category

    @property
    def meaning(self):
        """
        A description of this character.

        Where relevant, it will mention the character itself; otherwise,
        it will describe only the category.

        In cases where TeX gives a meaning in tex.web, we use the same
        representation.
        """
        return '?'

    def __str__(self):
        if self.ch is None:
            return '[ None ]'
        elif len(self.ch)==1:
            codepoint = ord(self.ch)
            if codepoint>=31 and codepoint<=126:
                return self.ch
            elif codepoint<128:
                return '^^%02x' % (codepoint,)
            else:
                return '[ %x ]' % (codepoint,)
        else:
            return self.ch

    def __repr__(self):
        return self.meaning

    def __eq__(self, other):
        if not isinstance(other, Token):
            return False

        return self.ch==other.ch and self.category==other.category

    @property
    def is_space(self):
        """
        Whether this is a <space token>, as defined on p265 of the TeXbook.
        """
        # TODO ...or a control sequence or active character whose
        # TODO current meaning has been made equal to a token of category=SPACE
        # TODO by \let or \futurelet.
        return self.category==self.SPACE

    @property
    def identifier(self):
        """
        The string by which you can look this symbol up in `doc[...]`.

        Only valid for active characters.
        """
        raise NotImplementedError(self.__class__.__name__)

    @classmethod
    def serialise_list(
            cls,
            tokens,
            strip_singleton=False,
        ):
        """
        Turns a list of Tokens into serialised form.

        Args:
            tokens: a list of Tokens
            strip_singleton: if True, and the result would have been
                a singleton list containing only a string, that string
                is returned instead of the list. Defaults to False.

        Returns:
            the serialised representation of "tokens".
            See the docstring for this class for the format specification.
        """

        defaults = yex.control.keyword.Catcode._default_contents()
        result = []

        for item in tokens:
            try:
                item.ch
                item.category
            except AttributeError:
                types = [(repr(x), type(x).__name__) for x in tokens]
                raise ValueError((
                    'List containing non-Tokens passed to '
                    f'Token.serialise_list: {types}'
                    ))

            addendum = None

            if isinstance(item, Control):
                addendum = [ item.identifier ]
                result.append( [
                    item.identifier,
                    ])

            elif isinstance(item, Argument):
                addendum = f'#{item.ch}'

            elif isinstance(item, Parameter):
                if item.ch=='#':
                    addendum = '##'
                else:
                    addendum = [ item.category, item.ch ]

            elif (len(item.ch)==1 and
                    item.category==defaults.get(ord(item.ch), cls.OTHER)):

                    # This is in the same category it was at the start.
                    # So we can put it just raw in a string.

                    addendum = item.ch

            else:
                addendum = [ item.category, item.ch ]

            if isinstance(addendum, str):
                if not result or not isinstance(result[-1], str):
                    result.append('')
                result[-1] += addendum
            else:
                result.append(addendum)

        if strip_singleton and len(result)==1 and isinstance(result[0], str):
            result = result[0]

        return result

    @classmethod
    def deserialise_list(
            cls,
            state,
            max_arg = 9,
        ):
        """
        Turns a serialised representation of a list of Tokens
        back into real Tokens.

        Args:
            state (list, or str, or Tokeniser): if a list, this is a
                representation of a series of Tokens; see the docstring
                for this class for the format specification. If a Tokeniser,
                this is read until exhaustion and treated in the same way.
                If a str, this is treated in the same way as if that str
                was a singleton member of a list.

                Items in this list which are already Tokens are
                passed through unchanged.

        Returns:
            a list of Tokens, as represented by the "state" argument.
        """

        defaults = yex.control.keyword.Catcode._default_contents()
        result = []

        if isinstance(state, str):
            state = [state]

        for item in state:
            if isinstance(item, cls):
                result.append(item)
            elif isinstance(item, str):
                arg_next = False
                for c in item:
                    if arg_next:
                        if '1' <= c <= '9':
                            arg = Argument(ch=c)

                            if arg.index>max_arg:
                                raise ValueError(
                                        f'Contains #{c}, but we can only '
                                        f'go up to {max_arg}.')
                            result.append( Argument(ch=c) )
                        elif c=='#':
                            result.append(Parameter(ch=c))
                        else:
                            raise ValueError(
                                    f'"#{c}" is an invalid sequence.')

                        arg_next = False
                    elif c=='#':
                        arg_next = True
                    else:
                        result.append(
                                cls.get( ch = c,
                                    category = defaults[ord(c)],
                                    ))

            elif isinstance(item, (list, tuple)):
                if len(item)==2:
                    result.append(
                            cls.get(
                                category = item[0],
                                ch = item[1],
                                ))
                elif len(item)==1:
                    result.append(
                            cls.get(
                                category = cls.CONTROL,
                                ch = item[0],
                                ))
                else:
                    raise ValueError(
                            'Lists representing Tokens must have '
                            f'1 or 2 elements: {item}')
            elif item is None and not isinstance(state, list):
                # we were created from a Tokeniser
                break
            else:
                raise TypeError(
                        f"Can't deserialise {state} into a token list, "
                        f"because item {item} (which is {type(item)}) "
                        "is not a Token, nor a str, nor a pair.")

        return result

    @classmethod
    def is_from_tex(cls):
        r"""
        Is this a standard TeX token category?

        Returns:
            True if this category exists in TeX; False if this is a
                yex extension.
        """
        return type(cls._category)==int

    @classmethod
    def get(
            cls,
            ch,
            category = None,
            location = None,
            ):
        r"""
        Creates and returns a token.

        Args:
            ch (`str`): The character represented by the token. Must be a
                string of length 1. At present, the character must have
                a codepoint between 0 and 255 inclusive.
            category (`int` or `None`): the TeX category of the new token.
                A list is given in the Token class.
                If this is None, the category is 10 for spaces (ASCII 32)
                and 10 for everything else.
                This rule is from p213 of the TeXbook.
            location (`yex.parse.Location` or `None`): the location
                this token was read from.
        """

        if ord(ch)<0 or ord(ch)>255:
            raise ValueError(
                    f"Codepoints must be between 0 and 255 (was {ord(ch)})")

        if category is None:
            # These are the only two options for strings; see
            # p213 of the TeXbook
            if ch==' ':
                cls = Space
            else:
                cls = Other
        else:
            if category not in Token.by_category:
                raise ValueError(f"Don't know token category: {category}")

            cls = Token.by_category[category]

        result = cls(
                ch = ch,
                location = location
                )

        return result

class Escape(Token):

    _category = Token.ESCAPE

    @property
    def meaning(self):
        return "escape character"

class BeginningGroup(Token):
    r"""
    A character that begins groups. By default, this is {.
    """
    _category = Token.BEGINNING_GROUP

    @property
    def meaning(self):
        return f"begin-group character {self.ch}"

class EndGroup(Token):
    r"""
    A character that ends groups. By default, this is }.
    """
    _category = Token.END_GROUP

    @property
    def meaning(self):
        return f"end-group character {self.ch}"

class MathShift(Token):
    r"""
    A character that shifts into inline maths.

    By default, this is $.
    """
    _category = Token.MATH_SHIFT

    @property
    def meaning(self):
        return f"math shift character {self.ch}"

class AlignmentTab(Token):
    r"""
    A character used for aligning tables.

    By default, this is &.
    """
    _category = Token.ALIGNMENT_TAB

    @property
    def meaning(self):
        return "end of alignment template"

# END_OF_LINE is handled internally

class Parameter(Token):
    r"""
    A character that precedes the number of a macro parameter.

    By default, this is #.

    It can only appear in macro parameters or macro definitions.
    """
    _category = Token.PARAMETER

    @property
    def meaning(self):
        return f"macro parameter character {self.ch}"

    @classmethod
    def handle_second(cls,
            second,
            max_index,
            ):
        if isinstance(second, cls):
            return second

        elif isinstance(second, Other):

            if '1' <= second.ch <= '9':
                index = ord(second.ch)-48

                if index <= max_index:
                    return Argument(second.ch)

            else:
                return None

        else:
            return None

class Superscript(Token):
    r"""
    A character that produces superscript text.

    By default, this is ^.
    """
    _category = Token.SUPERSCRIPT

    @property
    def meaning(self):
        return f"superscript character {self.ch}"

class Subscript(Token):
    r"""
    A character that produces subscript text.

    By default, this is _.
    """
    _category = Token.SUBSCRIPT

    @property
    def meaning(self):
        return f"subscript character {self.ch}"

# IGNORED is... well, ignored

class Space(Token):
    r"""
    A blank space character, such as ASCII 32.

    We might also represent this as ␣.
    """
    _category = Token.SPACE

    @property
    def meaning(self):
        return f"blank space {self.ch}"

class Letter(Token):
    r"""
    An alphabetical letter.

    By default, this covers A to Z and a to z.
    """
    _category = Token.LETTER

    @property
    def meaning(self):
        return f"the letter {self.ch}"

class Other(Token):
    r"""
    Some other valid character.

    By default, this includes all punctuation and all digits.
    """
    _category = Token.OTHER

    @property
    def meaning(self):
        return f"the character {self.ch}"

class Active(Token):

    _category = Token.ACTIVE

    @property
    def meaning(self):
        return f"the active character {self.ch}"

    @property
    def identifier(self):
        return self.ch

# COMMENT is handled internally
# and INVALID is, you've guessed it, invalid

class Control(Token):

    _category = Token.CONTROL

    def __init__(self, name,
            doc,
            location,
            ):
        self.name = name
        self.doc = doc
        self.location = location

    def __str__(self):
        return self.identifier

    @property
    def ch(self):
        return str(self)

    def set_from_tokens(self, tokens):
        raise yex.exception.CantAssignToItemError(
                item = self,
                )

    @property
    def identifier(self):
        if len(self.name)==1 and ord(self.name)<32:
            return '\\^'+chr(64+ord(self.name))
        return '\\'+self.name

    def __repr__(self):
        return self.identifier

class Internal(Token):
    """
    Special tokens which are part of yex's infrastructure.

    Unlike most tokens, these are callables. Expanders
    call them when they see them.
    """

    _category = Token.INTERNAL

    def __init__(self, *args):
        self.ch = self.identifier

    @property
    def identifier(self):
        return self.__class__.__name__

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

class Paragraph(Token):
    r"""
    Paragraph break.

    This can only be generated internally; it's not part of the TeX system.
    It exists to make yex's code simpler.

    It's never generated by the parser: reading "\par" does not generate
    one of these. Instead, it generates a yex.parse.Control for the symbol
    whose name is "\par".  Expander will look this up and discover
    yex.control.keyword.Par. When the Mode runs that, it will produce an
    instance of this class. Yes, that really is the best way to do it.
    """

    _category = Token.PARAGRAPH

    def __init__(self, *args):
        self.ch = self.identifier

    @property
    def identifier(self):
        return r'\par'

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '[paragraph]'

class Argument(Token):
    _category = Token.ARGUMENT

    @property
    def index(self):
        return ord(self.ch)-48

    def __repr__(self):
        return f'#{self.ch}'

Token.by_category = dict([
    (value._category, value) for value in Token.__subclasses__()
    ])
