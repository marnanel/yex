import collections
from mex.state import State

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
            category):

        if ord(ch)>255:
            raise ValueError("Codepoints above 255 are not yet supported")

        if category<0 or category>15:
            raise ValueError("Category numbers run from 0 to 15")

        self.ch = ch
        self.category = category

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
        else:
            raise ValueError(
                    f"impossible: category {self.category} does not exist")

    def __str__(self):

        if ord(self.ch)<32:
            the_char = ''
        else:
            the_char = f'({self.ch})'

        return '%6d %3s %s' % (
                ord(self.ch),
                the_char,
                self.meaning,
                )

class Control(Token):

    def __init__(self, name,
            state):
        self.name = name
        self.ch = None
        self.category = self.CONTROL
        self.state = state

    def __str__(self):
        return f'\\{self.name}'

    @property
    def macro(self):
        result = self.state[f'macro {self.name}']
        return result

class Parameter(Token):

    def __init__(self, number):
        self.number = number

    def __str__(self):
        return f'(#{self.number})'

class Tokeniser:

    def __init__(self,
            state,
            source,
            params = None):
        self.state = state

        self.state.add_block(
                'charcode',
                self.default_code_table(),
                )
        self.push_back = []
        self.source = source

        self._iterator = self._read(
                source,
                params)

    def __iter__(self):
        return self

    def __next__(self):
        return self._iterator.__next__()

    def default_code_table(self):
        result = {
                "\\":  0, # Escape character
                '{':   1, # Beginning of group
                '}':   2, # Beginning of group
                '$':   3, # Beginning of group
                '&':   4, # Beginning of group
                '\n':  5, # End of line
                '#':   6, # Parameter
                '^':   7, # Superscript
                '_':   8, # Subscript
                '\0':  9, # Ignored character
                ' ':  10, # Space
                # 11: Letter
                # 12: Other
                '~':  13, # Active character
                '%':  14, # Comment character
                chr(127): 15, # Invalid character,
                }

        for pair in [
                ('a', 'z'),
                ('A', 'Z'),
            ]:

            for c in range(ord(pair[0]), ord(pair[1])+1):
                result[chr(c)] = 11 # Letter

        return collections.defaultdict(
                lambda: 12, # Other
                result)

    def _read(self, f, params = None):

        c = None
        build_control_name = None
        build_line_to_eol = None
        build_number = ''
        build_number_base = None
        at_eol = None

        while True:

            if not params:
                params = {}

            if self.push_back:
                thing = self.push_back.pop()
                if isinstance(thing, Token):
                    params = yield thing
                    continue
                else:
                    c = thing
            else:
                c = f.read(1)

            category = self.state.values[-1]['charcode'][c]

            if build_control_name is not None:

                # Reading in a control name (after a backslash)

                if category==11: # Letter
                    build_control_name += c

                else:

                    if build_control_name=='':
                        params = yield Control(
                                name = c,
                                state = self.state,
                                )
                    else:
                        params = yield Control(
                                name = build_control_name,
                                state = self.state,
                                )
                        self.push(c)

                    build_control_name = None

            elif build_line_to_eol is not None:

                if c=='' or category==5: # eof, or end of line
                    if at_eol:
                        at_eol(build_line_to_eol)
                    build_line_to_eol = None
                    at_eol = None
                else:
                    build_line_to_eol += c

                if c=='': # eof
                    break

            else:
                if c=='': # eof
                    break
                elif category==0: # Escape
                    build_control_name = ''
                    continue
                elif category==14: # Comment
                    build_line_to_eol = ''
                    at_eol = None
                    continue

                params = yield Token(
                    ch = c,
                    category = category,
                    )

    def push(self, thing):
        """
        Pushes back a token or a character.

        If the generator is running, it will see the new thing
        first, before any of its regular input.

        If the thing is a character, it will be parsed as usual;
        if it's a token, it will simply be yielded.

        Multiple-character strings aren't supported, but
        maybe they should be.
        """
        if thing=='':
            # not pushing back eof
            return
        self.push_back.append(thing)

if __name__=='__main__':

    state = State()

    with open('texbook.tex', 'r') as f:
        t = Tokeniser(state = state)
        for c in t.read(f):
            print(c)
