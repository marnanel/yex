import mex.exception
import mex.parse.source
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
            category,
            source = None):

        if ord(ch)>255:
            raise ValueError(
                    f"Codepoints above 255 are not yet supported (was {ord(ch)})")

        if category<0 or category>15:
            raise ValueError(
                    f"Category numbers run from 0 to 15 (was {category})")

        self.ch = ch
        self.category = category
        self.source = source

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
            raise ValueError("can't compare Token and "+str(type(other)))

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
            source):
        self.state = state
        self.catcodes = state.registers['catcode']
        self.push_back = []

        if hasattr(source, 'read'):
            # File-like

            try:
                name = source.name
            except AttributeError:
                name = '?'

            # Here is a new record attempt for the number of times
            # you can write "source" on three lines
            self.source = mex.parse.source.FileSource(
                    source = source,
                    name = name)
        else:
            # An iterable, I suppose.
            # Reverse it and add it to the push_back list.
            name = '<str>'
            self.source = mex.parse.source.NullSource(
                    name=name,
                    )
            for t in reversed(source):
                self.push_back.append(t)

        self.state.get(
            'inputlineno',
            the_object_itself=True,
            ).source = self.source

        self._iterator = self._read()

    def __iter__(self):
        return self

    def __next__(self):
        return self._iterator.__next__()

    def _read(self):

        self._build_control_name = None
        self._skipping_comment = False
        self._build_parameter = False
        self._caret = None

        macro_logger.debug("210")
        yield from self._handle_pushback()
        macro_logger.debug("211")

        for c in self.source:
            macro_logger.debug("  -- read char: %s", c)
            macro_logger.debug("213")
            yield from self._handle_thing(c)
            macro_logger.debug("214")
            yield from self._handle_pushback()
            macro_logger.debug("215")

        macro_logger.debug("222")
        yield from self._handle_pushback()
        macro_logger.debug("223")
        yield from self._handle_thing(None)
        macro_logger.debug("224")

    def _handle_pushback(self):

        macro_logger.debug("  -- pushback now: %s", self.push_back)

        while self.push_back:
            thing = self.push_back.pop()
            macro_logger.debug("  -- read from pushback: %s", thing)

            if not isinstance(thing, str):
                yield thing
            else:
                yield from self._handle_thing(thing)

        self.push_back = []

    def _handle_thing(self, c):

        if self._caret is None and c=='^':
            self._caret = ''
            return
        elif self._caret is not None:

            if self._caret=='':

                if c!='^':
                    # We've already seen one self._caret ("^"),
                    # but it hasn't been followed by another,
                    # so emit the self._caret, then next time
                    # start again with interpreting this symbol.

                    self.push(c)

                    c = '^'
                    self._caret = None
                else:
                    # We saw two self._carets. Let's see what comes next.
                    self._caret = c
                    return

            elif len(self._caret)==1:

                # We've seen two self._carets plus one following symbol.
                # Two self._carets could be followed by two hex digits,
                # or by a single character.

                self._caret += c

                if c in string.hexdigits:
                    # So we've seen one hex digit. If there's another
                    # one on the way, then this is two hex digits.
                    # If it isn't, it's just another case of
                    # a single character.
                    #
                    # Go round again and see which it is.
                    return

                # Otherwise, fall through.

            else:
                # We've seen two self._carets, then one hex digit, then one
                # more following symbol. If the new symbol is also
                # a hex digit, then we have a hex literal as per
                # per p45 of the TeXbook.

                if c in string.hexdigits:
                    self._caret += c
                    if c in string.hexdigits:
                        self.push(chr(int(self._caret[1:3], 16)))
                        self._caret = None
                        return

                # Otherwise, the new symbol isn't part of the
                # self._caret sequence. Treat the first part (the hex digit)
                # as a single character.
                self.push(c)

            if self._caret:
                code = ord(self._caret[1])

                if code<64:
                    code += 64
                elif code<127:
                    code -= 64
                else:
                    raise mex.exception.ParseError("Don't know how to deal with "+\
                            f"{code} after ^^",
                            self)

                c = chr(code)
                self._caret = None

        category = self.catcodes.get_directly(c)

        if self._build_control_name is not None:
            macro_logger.debug("  -- BCN: %s", c)

            # Reading in a control name (after a backslash)

            if category==Token.LETTER:
                self._build_control_name += c
                macro_logger.debug("  -- BCN letter: %s", self._build_control_name)

            else:

                if self._build_control_name=='':
                    # This is a control symbol
                    # (a control sequence of one character,
                    # that character not being a letter).

                    macro_logger.debug("  -- BCN symbol: %s", c)
                    yield Control(
                            name = c,
                            state = self.state,
                            )
                else:
                    macro_logger.debug("  -- BCN done: %s", self._build_control_name)
                    if category!=Token.SPACE:
                        self.push(c)
                    yield Control(
                            name = self._build_control_name,
                            state = self.state,
                            )

                self._build_control_name = None

        elif c is None:
            return # EOF

        elif self._skipping_comment:
            if c=='' or category==Token.END_OF_LINE:
                self._skipping_comment = False

        elif self._build_parameter:
            self._build_parameter = False
            yield Parameter(ch=c)

        elif category==Token.ESCAPE:
            self._build_control_name = ''

        elif category==Token.COMMENT:
            self._skipping_comment = True

        elif category==Token.PARAMETER:
            self._build_parameter = True

        else:
            yield Token(
                ch = c,
                category = category,
                )

    def push(self, thing,
            clean_char_tokens = False):
        """
        Pushes back a token or a character.

        If the generator is running, it will see the new thing
        first, before any of its regular input.

        If the thing is a character, it will be parsed as usual;
        if it's a token, it will simply be yielded.

        If you supply a list (not just any iterable!) the
        contents of the list will be pushed as if you'd
        pushed them individually. Multi-character strings
        work similarly.

        If you set "clean_char_tokens", then all bare characters
        will be converted to the Tokens for those characters.
        (For example, 'T', 'e', 'X' -> ('T' 12) ('e' 12) ('X' 12).)
        The rules about how this is done are on p213 of the TeXbook.
        Otherwise, the characters will remain just characters
        and the tokeniser will tokenise them as usual when it
        gets to them.

        When the generator is exhausted, this method will
        continue to work, but you'll need to pop them off
        the stack yourself: it doesn't un-exhaust the generator.
        """
        if thing is None:
            macro_logger.debug("  -- not pushing back eof")
            return

        if not isinstance(thing, (list, str)):
            thing = [thing]

        if clean_char_tokens:

            def _clean(c):
                if not isinstance(c, str):
                    return c

                # These are the only two options for strings; see
                # p213 of the TeXbook
                if c==' ':
                    return Token(ch=c,
                            category=Token.SPACE)
                else:
                    return Token(ch=c,
                            category=Token.OTHER)

            thing = [_clean(c) for c in thing]

        macro_logger.debug("  -- push back: %s", thing)
        self.push_back.extend(
                list(reversed(thing)))

    def error_position(self, message):

        result = ''

        EXCERPT_WIDTH = 40

        line = self.source.lines[-1]
        column_number = self.source.column_number

        result += '%s:%3d:%4d:%s' % (
                self.source.name,
                column_number,
                self.source.line_number,
                message) + '\n'

        if column_number < EXCERPT_WIDTH//2:
            left = 0
        elif column_number > len(line)-EXCERPT_WIDTH//2:
            left = len(line)-EXCERPT_WIDTH
        else:
            left = column_number - EXCERPT_WIDTH//2

        result += line[left:left+EXCERPT_WIDTH] + '\n'
        result += ' '*(column_number-left)+"^\n"

        return result

    def eat_optional_spaces(self):
        """
        Eats zero or more space tokens.
        This is <optional spaces> on p264 of the TeXbook.

        """
        while self._maybe_eat_token(
                what = lambda c: c.is_space,
                log_message = 'skip whitespace',
                ):
            pass

    def eat_optional_equals(self):
        """
        Eats zero or more whitespace tokens, then optionally an
        equals sign.

        This is <equals> on p271 of the TeXbook.
        """
        self.eat_optional_spaces()
        self._maybe_eat_token(
                what = lambda c: c.category==c.OTHER and c.ch=='=',
                log_message = 'skip equals',
                )

    def _maybe_eat_token(self, what,
            log_message='Eaten'):
        """
        Examines the next token. If what(token) is True,
        return True. Otherwise, push the token back and
        return False.

        If we're at EOF, return False.
        """
        try:
            token = self._iterator.__next__()
        except StopIteration:
            return False

        macro_logger.debug('   -- -- %s %s', token.category, token.ch)
        macro_logger.debug('   -- -- %s %s', token.category==token.OTHER, token.ch=='=')
        if what(token):
            macro_logger.debug("  -- Yes %s: %s",
                    log_message, token)
            return True
        else:
            macro_logger.debug("  -- No")
            self.push(token)
            return False

    def optional_string(self, s):

        pushback = []

        for letter in s:
            try:
                c = self._iterator.__next__()
            except StopIteration:
                return False

            pushback.append(c)

            if c.ch!=letter:
                self.push(pushback)
                return False

        return True

    def __repr__(self):
        result = f'[Tokeniser;{self.source}'

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
