import yex.exception
import logging

logger = logging.getLogger('yex.general')

class Token:
    r"""
    A categorised symbol.

    The tokeniser runs through the files it reads, categorising each character
    into one of these groups. It uses a lookup table in
    `yex.register.CatcodesTable` for this. You can find the default values
    over there.

    A few groups are never used outside the tokeniser; the rest have
    subclasses within this module.
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

    def __init__(self,
            ch,
            location = None):

        if type(self)==Token:
            raise ValueError("Don't instantiate Tokens directly")

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
        raise NotImplementedError()

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
        return f'\\{self.name}'

    def __repr__(self):
        return str(self)

    @property
    def ch(self):
        return str(self)

    def set_from_tokens(self, tokens):
        raise yex.exception.ParseError(
                f"you cannot assign to {self}")

    @property
    def identifier(self):
        return '\\'+self.name

class Internal(Token):
    """
    Special tokens which are part of yex's infrastructure.

    Unlike most tokens, these are callables. Expanders
    call them when they see them.
    """

    _category = Token.INTERNAL

    def __init__(self, *args):
        self.ch = self.__class__.__name__

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

class Paragraph(Token):
    """
    Paragraph break.

    This can only be generated internally; it's not part of the TeX system.
    It exists to make yex's code simpler.
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

g = list(Token.__subclasses__())

tokens_by_category = dict([
    (value._category, value) for value in g
    ])

def get_token(
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
            and 10 for everything else. This rule is from p213 of the TeXbook.
        location (`yex.parse.source.Location` or `None`): the location
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
        if category not in tokens_by_category:
            raise ValueError(f"Don't know token category: {category}")

        cls = tokens_by_category[category]

    result = cls(
            ch = ch,
            location = location
            )

    return result
