import mex.exception
import logging
import string

macro_logger = logging.getLogger('mex.macros')

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

    def __repr__(self):
        return str(self)

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
        self.catcodes = state.catcode
        self.push_back = []

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
                macro_logger.debug("  -- read from pushback: %s", thing)
                if not isinstance(thing, str):
                    params = yield thing
                    continue
                else:
                    c = thing
            elif f is None:
                macro_logger.debug("  -- reached eof")
                break
            else:
                c = f.read(1)

                if c=='\n':
                    self.state.lineno += 1

                macro_logger.debug("  -- read char: %s", c)

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
                        # We saw two carets. Let's see what comes next.
                        caret = c
                        continue
                elif len(caret)==1:

                    # We've seen two carets plus one following symbol.
                    # Two carets could be followed by two hex digits,
                    # or by a single character.

                    caret += c

                    if c in string.hexdigits:
                        # So we've seen one hex digit. If there's another
                        # one on the way, then this is two hex digits.
                        # If it isn't, it's just another case of
                        # a single character.
                        #
                        # Go round again and see which it is.
                        continue

                    # Otherwise, fall through.

                else:
                    # We've seen two carets, then one hex digit, then one
                    # more following symbol. If the new symbol is also
                    # a hex digit, then we have a hex literal as per
                    # per p45 of the TeXbook.

                    if c in string.hexdigits:
                        caret += c
                        if c in string.hexdigits:
                            self.push(chr(int(caret[1:3], 16)))
                            caret = None
                            continue

                    # Otherwise, the new symbol isn't part of the
                    # caret sequence. Treat the first part (the hex digit)
                    # as a single character.
                    self.push(c)

                if caret:
                    code = ord(caret[1])

                    if code<64:
                        code += 64
                    elif code<127:
                        code -= 64
                    else:
                        raise mex.exception.ParseError("Don't know how to deal with "+\
                                f"{code} after ^^",
                                self)

                    c = chr(code)
                    caret = None

            category = self.catcodes.get_directly(c)

            if build_control_name is not None:

                # Reading in a control name (after a backslash)

                if category==Token.LETTER:
                    build_control_name += c

                else:

                    if build_control_name=='':
                        # This is a control symbol
                        # (a control sequence of one character,
                        # that character not being a letter).

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

        If you supply a list (not just any iterable!) the
        contents of the list will be pushed as if you'd
        pushed them individually.

        Multiple-character strings aren't supported, but
        maybe they should be.

        When the generator is exhausted, this method will
        continue to work, but you'll need to pop them off
        the stack yourself: it doesn't un-exhaust the generator.
        """
        if isinstance(thing, str):

            if thing=='':
                macro_logger.debug("  -- not pushing back eof")
                return

            if thing=='\n':
                self.state.lineno -= 1

        if isinstance(thing, list):
            macro_logger.debug("  -- push back list: %s", thing)
            self.push_back.extend(
                    list(reversed(thing)))
        else:
            macro_logger.debug("  -- push back item: %s", thing)
            self.push_back.append(thing)

    def error_position(self, message):
        result = '%3d:%s' % (self.state.lineno, message)

        return result

    def __repr__(self):
        result = '[Tokeniser'

        try:
            source = self.source.name
        except:
            source = 'str'

        result += ';%s:%d' % (
                source, self.state.lineno)
        if self.push_back:
            result += ';pb='+repr(self.push_back)
        result += ']'
        return result


if __name__=='__main__':

    import mex.state
    state = mex.state.State()

    with open('texbook.tex', 'r') as f:
        t = Tokeniser(state = state)
        for c in t.read(f):
            print(c)
