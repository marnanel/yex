import collections

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

    def __eq__(self, other):
        if not isinstance(other, Token):
            raise ValueError("can't compare Token and "+str(type(other)))

        return self.ch==other.ch and self.category==other.category

class Control(Token):

    def __init__(self, name,
            state):
        self.name = name
        self.category = self.CONTROL
        self.state = state

    def __str__(self):
        return f'\\{self.name}'

    @property
    def ch(self):
        return str(self)

    @property
    def macro(self):
        result = self.state[f'macro {self.name}']
        return result

class Parameter(Token):

    def __init__(self, ch):
        self.ch = ch
        self.category = self.PARAMETER

    def __str__(self):
        return f'(#{self.ch})'

class Tokeniser:

    def __init__(self,
            state,
            source,
            params = None):
        self.state = state
        self.push_back = []

        self.state.add_block(
                'charcode',
                self.default_code_table(),
                )

        if hasattr(source, 'read'):
            # File-like
            self.source = source
            self.push_back = []
        else:
            # An iterable, I suppose.
            # Reverse it and add it to the push_back list.
            self.source = None
            for t in reversed(source):
                self.push_back.append(t)

        self._iterator = self._read(
                self.source,
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
        build_parameter = False
        at_eol = None
        caret = None

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
            elif f is None:
                return
            else:
                c = f.read(1)

            if caret is None and c=='^':
                caret = ''
                continue
            elif caret is not None:

                if caret=='':

                    if c!='^':
                        # We've already seen one caret ("^"),
                        # but it hasn't been followed by another,
                        # so emit the caret, then next time
                        # start again with interpreting this symbol.

                        self.push(c)

                        c = '^'
                        caret = None
                    else:
                        caret = c
                        continue
                else:
                    # So we've just seen "^^".
                    # Interpret the next character per p45 of the TeXbook.

                    HEX = '0123456789abcdef'

                    if len(caret)==2:
                        caret += c
                        if c in HEX:
                            c = chr(int(caret[1:3], 16))
                            caret = None
                        else:
                            raise ValueError(f"invalid hex number: {caret}")
                    else:
                        if c in HEX:
                            caret += c
                            continue

                        code = ord(c)

                        if code<64:
                            code += 64
                        elif code<127:
                            code -= 64
                        else:
                            raise ValueError("Don't know how to deal with "+\
                                    f"{code} after ^^")

                        c = chr(code)
                        caret = None

            category = self.state.values[-1]['charcode'][c]

            if build_control_name is not None:

                # Reading in a control name (after a backslash)

                if category==Token.LETTER:
                    build_control_name += c

                else:

                    if build_control_name=='':
                        params = yield Control(
                                name = c,
                                state = self.state,
                                )
                    else:
                        if category!=Token.SPACE:
                            self.push(c)
                        params = yield Control(
                                name = build_control_name,
                                state = self.state,
                                )

                    build_control_name = None

            elif build_line_to_eol is not None:

                if c=='' or category==Token.END_OF_LINE:
                    if at_eol:
                        at_eol(build_line_to_eol)
                    build_line_to_eol = None
                    at_eol = None
                else:
                    build_line_to_eol += c

                if c=='': # eof
                    break

            elif build_parameter:

                build_parameter = False

                yield Parameter(ch=c)

            elif c=='': # eof
                break
            elif category==Token.ESCAPE:
                build_control_name = ''
            elif category==Token.COMMENT:
                build_line_to_eol = ''
                at_eol = None
            elif category==Token.PARAMETER:
                build_parameter = True
            else:
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
        if isinstance(thing, str) and thing=='':
            # not pushing back eof
            return
        self.push_back.append(thing)

if __name__=='__main__':

    import mex.state
    state = mex.state.State()

    with open('texbook.tex', 'r') as f:
        t = Tokeniser(state = state)
        for c in t.read(f):
            print(c)
