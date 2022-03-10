import mex.exception
import mex.parse.source
from mex.parse.tokenstream import Tokenstream
from mex.parse.token import Token, Control
import logging
import string

macros_logger = logging.getLogger('mex.macros')

class Tokeniser(Tokenstream):

    # Line statuses.
    # These are defined on p46 of the TeXbook, which calls
    # them "states". We call them line statuses, so as not
    # to confuse them with mex.state.State.
    BEGINNING_OF_LINE = 'N'
    MIDDLE_OF_LINE = 'M'
    SKIPPING_SPACES = 'S'

    def __init__(self,
            state,
            source):

        self.state = state
        self.catcodes = state.registers['catcode']
        self.push_back = []

        self.line_status = self.BEGINNING_OF_LINE

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
        self._caret = None

        macros_logger.debug("%s: tokeniser ready",
                self)

        eof_sent = 0

        while True:
            for c in self.source:
                macros_logger.debug("%s: handle char: %s",
                        self, c)
                yield from self._handle_thing(c)
                break
            else:
                macros_logger.debug("%s: handle None for eof",
                        self)
                yield from self._handle_thing(None)
                eof_sent += 1
                # prevent spinning if they're not checking
                # whether they're getting None
                if eof_sent > 5:
                    macros_logger.critical(
                            "spinning on eof; aborting")
                    return

            if self.push_back:
                    eof_sent = 0
            yield from self._handle_pushback()

    def _handle_pushback(self):

        while self.push_back:
            thing = self.push_back.pop()
            macros_logger.debug("%s: read from pushback: %s",
                    self, thing)

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
                            f"{code} after ^^")

                c = chr(code)
                self._caret = None

        category = self.catcodes.get_directly(c)

        if self._build_control_name is not None:

            # Reading in a control name (after a backslash)

            if category==Token.LETTER:
                self._build_control_name += c

            else:

                if self._build_control_name=='':
                    # This is a control symbol
                    # (a control sequence of one character,
                    # that character not being a letter).

                    yield Control(
                            name = c,
                            state = self.state,
                            )
                else:
                    if category!=Token.SPACE:
                        self.push(c)
                    yield Control(
                            name = self._build_control_name,
                            state = self.state,
                            )

                self._build_control_name = None

        elif c is None:
            yield None # EOF

        elif self._skipping_comment:
            if c=='' or category==Token.END_OF_LINE:
                self._skipping_comment = False

        elif category==Token.ESCAPE:
            self._build_control_name = ''

        elif category==Token.COMMENT:
            self._skipping_comment = True

        else:
            yield Token(
                ch = c,
                category = category,
                )

    def push(self, thing,
            clean_char_tokens = False):
        """
        Pushes back a token or a character.

        If the generator is expand, it will see the new thing
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

        This method works even if the file we're tokenising
        has ended.
        """
        if thing is None:
            macros_logger.debug("%s: not pushing back eof",
                    self)
            return

        if not isinstance(thing, (list, str)):
            thing = [thing]

        if clean_char_tokens:

            def _clean(c):
                if isinstance(c, str):
                    return Token(ch=c)
                else:
                    return c

            thing = [_clean(c) for c in thing]

        macros_logger.debug("%s: push back: %s",
                self, thing)
        self.push_back.extend(
                list(reversed(thing)))

    def error_position(self, message):

        def _screen_width():
            try:
                # https://bytes.com/topic/python/answers/837969-unable-see-os-environ-columns
                import sys,fcntl,termios,struct
                data = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, '1234')
                return struct.unpack('hh',data)[1]
            except:
                return 80

        result = ''

        EXCERPT_WIDTH = _screen_width()-1

        line = self.source.lines[-1]
        column_number = self.source.column_number

        result += '%s:%3d:%4d:%s' % (
                self.source.name,
                column_number,
                self.source.line_number,
                message) + '\n'

        if len(line)<EXCERPT_WIDTH:
            left = 0
        elif column_number < EXCERPT_WIDTH//2:
            left = 0
        elif column_number > len(line)-EXCERPT_WIDTH//2:
            left = len(line)-EXCERPT_WIDTH
        else:
            left = column_number - EXCERPT_WIDTH//2

        result += line[left:left+EXCERPT_WIDTH].rstrip() + '\n'
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
        token = self._iterator.__next__()

        if token is None:
            macros_logger.debug("    -- %s: eof",
                    log_message)
            return False
        elif what(token):
            macros_logger.debug("    -- %s: %s",
                    log_message, token)
            return True
        else:
            self.push(token)
            return False

    def optional_string(self, s):

        pushback = []

        macros_logger.debug("%s: checking for string: %s",
                self,
                s)

        for letter in s:
            for c in self._iterator:
                break

            if c is None:
                macros_logger.debug(
                        "%s: reached EOF; push back and return False: %s",
                        self,
                        pushback)

                self.push(pushback)
                return False

            pushback.append(c)

            if c.ch!=letter:
                self.push(pushback)
                macros_logger.debug(
                        (
                            "%s: %s doesn't match; "
                            "pushed back; will return False"
                            ),
                        self,
                        c.ch,)

                return False

        return True

    def __repr__(self):
        result = f'[tok;ls={self.line_status};{self.source}'

        if self.push_back:
            result += ';pb='+repr(self.push_back)
        result += ']'
        return result
