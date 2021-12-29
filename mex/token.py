import collections
from mex.state import State

class Token:

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
        if self.category==0:
            return 'Escape character'
        elif self.category==1:
            return 'Beginning of group'
        elif self.category==2:
            return 'End of group'
        elif self.category==3:
            return 'Math shift'
        elif self.category==4:
            return 'Alignment tab'
        elif self.category==5:
            return 'End of line'
        elif self.category==6:
            return 'Parameter'
        elif self.category==7:
            return 'Superscript'
        elif self.category==8:
            return 'Subscript'
        elif self.category==9:
            return 'Ignored character'
        elif self.category==10:
            return 'Space'
        elif self.category==11:
            return 'Letter'
        elif self.category==12:
            return 'Other character'
        elif self.category==13:
            return 'Active character'
        elif self.category==14:
            return 'Comment character'
        elif self.category==15:
            return 'Invalid character'
        else:
            raise ValueError(
                    f"impossible: category {self.category} does not exist")

    def __repr__(self):

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

    def __init__(self, name):
        self.name = name
        self.ch = None
        self.category = None

    def __str__(self):
        return f'\\{self.name}'

class Parameter(Token):

    def __init__(self, number):
        self.number = number

    def __str__(self):
        return f'(#{self.number})'

class Tokeniser:

    def __init__(self,
            state):
        self.state = state
        self.state.add_state(
                'charcode',
                self.default_code_table(),
                )

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

            for c in range(ord(pair[0]), ord(pair[1])):
                result[chr(c)] = 11 # Letter

        return collections.defaultdict(
                lambda: 12, # Other
                result)

    def read(self, f):

        c = None
        build_control_name = None
        build_line_to_eol = None
        push_back = []
        at_eol = None

        while True:

            if push_back:
                c = pushback.pop()
            else:
                c = f.read(1)

            category = self.state.values[-1]['charcode'][c]

            if build_control_name is not None:

                # Reading in a control name (after a backslash)

                if category==11: # Letter
                    build_control_name += c

                else:

                    if build_control_name=='':
                        yield Control(
                                name = c,
                                )
                    else:
                        yield Control(
                                name = build_control_name,
                                )
                        push_back.append(c)

                    build_control_name = None

            elif build_line_to_eol is not None:

                if c=='' or category==5: # eof, or end of line
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
                    at_eol = lambda x: print('Comment:', x)
                    continue

                yield Token(
                    ch = c,
                    category = category,
                    )

if __name__=='__main__':

    state = State()

    with open('texbook.tex', 'r') as f:
        t = Tokeniser(state = state)
        for c in t.read(f):
            print(c)
