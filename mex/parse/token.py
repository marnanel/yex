import mex.exception
import logging

macros_logger = logging.getLogger('mex.macros')

class Token:

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

    CONTROL = {}

    def __init__(self,
            ch,
            category = None,
            location = None):

        if ord(ch)>255:
            raise ValueError(
                    f"Codepoints above 255 are not yet supported (was {ord(ch)})")

        if category is None:
            # These are the only two options for strings; see
            # p213 of the TeXbook
            if ch==' ':
                category=self.SPACE
            else:
                category=self.OTHER

        elif category<0 or category>15:
            raise ValueError(
                    f"Category numbers run from 0 to 15 (was {category})")

        self.ch = ch
        self.category = category
        self.location = location

    @property
    def meaning(self):
        if self.category==self.ESCAPE:
            return 'Escape character'
        elif self.category==self.BEGINNING_GROUP:
            return 'Beginning of group'
        elif self.category==self.END_GROUP:
            return 'End of group'
        elif self.category==self.MATH_SHIFT:
            return 'Math shift'
        elif self.category==self.ALIGNMENT_TAB:
            return 'Alignment tab'
        elif self.category==self.END_OF_LINE:
            return 'End of line'
        elif self.category==self.PARAMETER:
            return 'Parameter'
        elif self.category==self.SUPERSCRIPT:
            return 'Superscript'
        elif self.category==self.SUBSCRIPT:
            return 'Subscript'
        elif self.category==self.IGNORED:
            return 'Ignored character'
        elif self.category==self.SPACE:
            return 'Space'
        elif self.category==self.LETTER:
            return 'Letter'
        elif self.category==self.OTHER:
            return 'Other character'
        elif self.category==self.ACTIVE:
            return 'Active character'
        elif self.category==self.COMMENT:
            return 'Comment character'
        elif self.category==self.INVALID:
            return 'Invalid character'
        elif self.category==self.CONTROL:
            return 'Control'
        else:
            raise ValueError(
                    f"impossible: category {self.category} does not exist")

    def __str__(self):

        try:
            codepoint = ord(self.ch)
            if codepoint<32:
                the_char = ''
            else:
                the_char = f'({self.ch})'
        except TypeError:
            codepoint = 0
            the_char = f'({self.ch})'

        return '%6d %3s %s' % (
                codepoint,
                the_char,
                self.meaning,
                )

    def __repr__(self):

        if self.ch is not None and len(self.ch)==1 and ord(self.ch)<31:
            return "[%d %s]" % (
                    ord(self.ch),
                    self.meaning,
                    )
        elif self.category in (self.LETTER, self.OTHER):
            return "[%s]" % (
                    self.ch,
                    )
        else:
            return "[%s %s]" % (
                    self.ch,
                    self.meaning,
                    )

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

class Control(Token):

    def __init__(self, name,
            state,
            location,
            ):
        self.name = name
        self.category = self.CONTROL
        self.state = state
        self.location = location

    def __str__(self):
        return f'\\{self.name}'

    def __repr__(self):
        return str(self)

    @property
    def ch(self):
        return str(self)

    def set_from_tokens(self, tokens):
        raise mex.exception.ParseError(
                f"you cannot assign to {self}")


if __name__=='__main__':

    import mex.state
    state = mex.state.State()

    with open('texbook.tex', 'r') as f:
        t = Tokeniser(state = state)
        for c in t.read(f):
            print(c)
