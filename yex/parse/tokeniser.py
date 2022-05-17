import yex.exception
import yex.parse.source
from yex.parse.tokenstream import Tokenstream
from yex.parse.token import *
import logging
import string
import io

logger = logging.getLogger('yex.general')

HEX_DIGITS = string.hexdigits[:-6] # lose capitals

class Tokeniser(Tokenstream):

    # Line statuses.
    # These are defined on p46 of the TeXbook.
    BEGINNING_OF_LINE = 'N'
    MIDDLE_OF_LINE = 'M'
    SKIPPING_BLANKS = 'S'

    def __init__(self,
            doc,
            source):

        self.doc = doc
        self.catcodes = doc.registers['catcode']

        self.line_status = self.BEGINNING_OF_LINE

        try:
            name = source.name
        except AttributeError:
            name = '?'

        if hasattr(source, 'read'):
            # File-like

            # Here is a new record attempt for the number of times
            # you can write "source" on three lines
            self.source = yex.parse.source.FileSource(
                    f = source,
                    name = name)
        elif hasattr(source, '__getitem__') and not isinstance(source, str):
            self.source = yex.parse.source.ListSource(
                    contents = source,
                    name = name,
                    )
        else:
            # An iterable, I suppose.
            self.source = yex.parse.source.StringSource(
                    string = str(source),
                    )

        self.source.line_number_setter = doc[r'\inputlineno'].update
        self.location = None
        self._iterator = self._read()

    def __iter__(self):
        return self

    def __next__(self):
        result = next(self._iterator)
        try:
            self.location = result.location
        except AttributeError:
            pass
        return result

    def _get_category(self, c):
        if isinstance(c, str):
            return self.catcodes.get_directly(c)
        else:
            return Token.END_OF_LINE

    def correct_line_number(self):
        r"""
        Assigns the correct line number for \inputlineno.

        You only need to call this if you've already changed it temporarily:
        for example, by doing an \input. Otherwise, it updates automatically.

        Args:
            None.

        Returns:
            `None.`
        """
        if self.source.line_number_setter is not None and \
                self.source.line_number is not None:
            self.source.line_number_setter(self.source.line_number)

    def _read(self):
        # See p46ff of the TeXbook for this algorithm.

        logger.debug("%s: tokeniser ready",
                self)

        for c in self.source: # never exhausts

            if not isinstance(c, str):
                yield c
                continue

            category = self._get_category(c)

            logger.debug("%s: received %s, %s",
                    self, c, category)

            if category in (
                    Token.BEGINNING_GROUP,
                    Token.END_GROUP,
                    Token.MATH_SHIFT,
                    Token.ALIGNMENT_TAB,
                    Token.PARAMETER,
                    Token.SUBSCRIPT,
                    Token.LETTER,
                    Token.OTHER,
                    Token.ACTIVE,
                    ):

                new_token = get_token(
                    ch = c,
                    category = category,
                    location = self.source.location,
                    )
                logger.debug("%s:   -- yield %s",
                        self, new_token)
                yield new_token

                self.line_status = self.MIDDLE_OF_LINE

            elif category==Token.END_OF_LINE:

                if self.line_status==self.BEGINNING_OF_LINE:
                    logger.debug("%s:   -- paragraph break",
                            self)

                    yield Control(
                            name = 'par',
                            doc = self.doc,
                            location = self.source.location,
                            )

                elif self.line_status==self.MIDDLE_OF_LINE:
                    logger.debug("%s:   -- EOL, treated as space",
                            self)

                    yield get_token(
                            ch = chr(32),
                            category = Token.SPACE,
                            location = self.source.location,
                            )
                else:
                    logger.debug("%s:   -- ignored",
                            self)

                self.line_status = self.BEGINNING_OF_LINE

            elif category==Token.SPACE:

                if self.line_status==self.MIDDLE_OF_LINE:
                    logger.debug("%s:   -- space",
                            self)

                    yield get_token(
                            ch = chr(32), # in spec
                            category = Token.SPACE,
                            location = self.source.location,
                            )
                    self.line_status = self.SKIPPING_BLANKS
                else:
                    logger.debug("%s:   -- ignored",
                            self)

            elif category==Token.ESCAPE:

                logger.debug("%s:   -- first char of escape: %s, %s",
                        self, c, category)

                name = ''
                for c2 in self.source:
                    category2 = self._get_category(c2)
                    logger.debug("%s:   -- and %s, %s",
                            self, c2, category2)

                    if category2==Token.END_OF_LINE and name=='':
                        break
                    elif category2==Token.LETTER:
                        name += c2
                    elif category2==Token.SUPERSCRIPT:
                        self._handle_caret(c2)
                    else:
                        break

                if name=='':
                    try:
                        name = c2.ch
                    except AttributeError:
                        name = str(c2)
                else:
                    while category2==Token.SPACE:
                        logger.debug("%s:     -- absorbing space",
                                self)
                        c2 = next(self.source)
                        category2 = self._get_category(c2)

                    self.source.push([c2])

                logger.debug("%s:     -- so the control is named %s",
                        self, name)

                new_token = Control(
                        name = name,
                        doc = self.doc,
                        location=self.source.location,
                        )

                logger.debug("%s:     -- producing %s",
                        self, new_token)

                yield new_token
                self.line_status = self.MIDDLE_OF_LINE

            elif category==Token.COMMENT:

                for c2 in self.source:
                    if c2 is None:
                        break

                    category2 = self._get_category(c2)
                    logger.debug("%s:   -- eating comment: %s, %s ",
                            self, c2, category2)

                    if category2==Token.END_OF_LINE:
                        self.line_status = self.BEGINNING_OF_LINE
                        break

            elif category==Token.SUPERSCRIPT:
                self._handle_caret(c)
                self.line_status = self.MIDDLE_OF_LINE

            elif category==Token.INVALID:
                logger.debug("%s:   -- invalid",
                        self)

                command_logger.warning("Invalid character found: %s", c)

            elif category==Token.IGNORED:
                logger.debug("%s:   -- ignored",
                        self)

            else:
                logger.debug("%s:   -- unknown!",
                        self)
                raise yex.exception.ParseError(
                        "Unknown category: %s is %s",
                        c, category)

    def _handle_caret(self, first):
        """
        Handles a char of category 7, SUPERSCRIPT. (In practice, this
        is usually a caret, ASCII 136.) This is complicated enough
        that it gets its own method.

        When this method is called, we have just seen the first caret,
        with ASCII code 136. When it returns, it will have modified
        the pushback so that the correct characters will be read next.
        The algorithm is given on p46 of the TeXbook.

        However, to avoid infinite recursion, if the immediate next
        character has the same character code as "first", this character
        will have been pushed as a Token with that character code and
        category 7, SUPERSCRIPT. In that case, we return True.
        Otherwise, we return False.
        """

        def _back_out():
            nonlocal result

            if result[0]==first:
                push_token = first
                result = result[1:]
            else:
                push_token = None

            self.push(result)

            if push_token is not None:
                logger.debug(
                        "%s:   -- pushing %s as Token to avoid recursion",
                        self, push_token)
                self.push(get_token(
                        ch = push_token,
                        category = Token.SUPERSCRIPT,
                        location = self.source.location,
                        ))

            return push_token is not None

        logger.debug("%s:   -- first character of caret: %s",
                self, first)

        result = [first, next(self.source)]

        logger.debug("%s:   -- second character of caret: %s",
                self, result[1])

        if result[0]!=result[1]:
            # the two characters must have the same code; it's not enough
            # that they're both of category SUPERSCRIPT
            logger.debug("%s:   -- they don't match; emitting first",
                    self)
            return _back_out()

        result.append(next(self.source))
        logger.debug("%s:   -- third character of caret: %s",
            self, result[2])

        try:
            third_codepoint = ord(result[2])
        except:
            logger.debug("%s:     -- not a char")
            return _back_out()

        if result[2] in HEX_DIGITS:
            result.append(next(self.source))
            logger.debug("%s:   -- fourth character of caret: %s",
                self, result[3])

            try:
                ord(result[3])
            except:
                logger.debug("%s:     -- not a char")
                return _back_out()

            if result[3] in HEX_DIGITS:
                result = [
                        chr(int(result[2]+result[3], 16))
                ]
                logger.debug("%s:   -- yes, this is a hex pair",
                    self)

                return _back_out()

        if third_codepoint<64:
            result = [chr(third_codepoint+64)] + result[3:]
        elif third_codepoint<128:
            result = [chr(third_codepoint-64)] + result[3:]

        return _back_out()

    def push(self, thing,
            clean_char_tokens = False):
        """
        Pushes back a token or a character.

        If the generator is expanding, it will see the new thing
        first, before any of its regular input.

        If the thing is a character, it will be parsed as usual;
        if it's a token, it will simply be yielded.

        If you supply a list (not just any iterable!) the
        contents of the list will be pushed as if you'd
        pushed them individually. Multi-character strings
        work similarly.

        If you set "clean_char_tokens", then all bare characters
        will be converted to the Tokens for those characters.s
        (For example, 'T', 'e', 'X' -> ('T' 12) ('e' 12) ('X' 12).)
        The rules about how this is done are on p213 of the TeXbook.
        Otherwise, the characters will remain just characters
        and the tokeniser will tokenise them as usual when it
        gets to them.

        This method works even if the file we're tokenising
        has ended.
        """
        if thing is None:
            logger.debug("%s: not pushing back eof",
                    self)
            return

        if not isinstance(thing, (list, str)):
            thing = [thing]

        if clean_char_tokens:

            def _clean(c):
                if isinstance(c, str):
                    return get_token(
                            ch=c,
                            location=self.source.location,
                            )
                else:
                    return c

            thing = [_clean(c) for c in thing]

        logger.debug("%s: push back: %s",
                self, thing)
        self.source.push(thing)

    def _single_error_position(self, frame, caller):

        def _screen_width():
            try:
                import sys,fcntl,termios,struct
                data = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, '1234')
                return struct.unpack('hh',data)[1]
            except:
                return 80

        FORMAT = (
                'File "%(filename)s", line %(line)d, in %(macro)s:\n'
                '  %(code)s\n'
                '  %(indent)s^\n'
                )

        EXCERPT_WIDTH = _screen_width()-1

        if frame.location is None:
            return f'In {caller}:\n  no frame information\n'

        # FIXME This will break if they're in separate files.
        # FIXME Make Source account for that.
        try:
            line = self.source.lines[frame.location.line]
        except IndexError:
            line = '(?)'
        column_number = self.source.column_number

        if len(line)<EXCERPT_WIDTH:
            left = 0
        elif column_number < EXCERPT_WIDTH//2:
            left = 0
        elif column_number > len(line)-EXCERPT_WIDTH//2:
            left = len(line)-EXCERPT_WIDTH
        else:
            left = column_number - EXCERPT_WIDTH//2

        code = line[left:left+EXCERPT_WIDTH].rstrip()
        indent = ' '*(frame.location.column-left)

        result = FORMAT % {
                'filename': frame.location.filename,
                'line': frame.location.line,
                'macro': caller,
                'code': code,
                'indent': indent,
                }

        return result

    def error_position(self, message):

        def callee_name(index):
            try:
                return str(self.doc.call_stack[index].callee)
            except IndexError:
                return 'bare code'

        result = ''

        result += self._single_error_position(
                yex.document.Callframe(
                    callee = None,
                    args = [],
                    location = self.location,
                    ),
                callee_name(-1),
                )

        # ...and our positions going back down the call stack.
        for i, frame in enumerate(reversed(self.doc.call_stack)):

            result += self._single_error_position(
                frame,
                callee_name(-2-i),
                )

        result += f'Error: {message}\n'

        return result

    def eat_optional_spaces(self):
        """
        Eats zero or more space tokens.
        This is <optional spaces> on p264 of the TeXbook.

        """
        while self._maybe_eat_token(
                what = lambda c: isinstance(c, Token) and c.is_space,
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
                what = lambda c: isinstance(c, Other) and c.ch=='=',
                log_message = 'skip equals',
                )

    def get_natural_number(self):
        """
        Reads and returns a decimal natural number.

        The number is a series of digits from 0 to 9. If the first digit
        is 0, it will be accepted on its own. Otherwise, we keep going
        until we see a non-digit, or until EOF.

        This is not how you read in numbers in general.
        For that, see `yex.value.Number`.

        Returns:
            the number represented by the string we found, or None
            if the first character we found wasn't a digit.
        """

        token = next(self._iterator)

        def is_a_digit(token):
            return isinstance(token, Token) and \
                    token.category==token.OTHER and \
                    token.ch in string.digits

        if not is_a_digit(token):
            return None
        elif token.ch=='0':
            return 0

        result = ''

        while is_a_digit(token):
            result += token.ch
            token = next(self._iterator)

        return int(result)

    def _maybe_eat_token(self, what,
            log_message='Eaten'):
        """
        Examines the next token. If what(token) is True,
        return True. Otherwise, push the token back and
        return False.

        If we're at EOF, return False.
        """
        token = next(self._iterator)

        if token is None:
            logger.debug("    -- %s: eof",
                    log_message)
            return False
        elif what(token):
            logger.debug("    -- %s: %s",
                    log_message, token)
            return True
        else:
            self.push(token)
            return False

    def optional_string(self, s):

        pushback = []
        c = None

        logger.debug("%s: checking for string: %s",
                self,
                s)

        def _inner():
            for letter in s:
                c = next(self._iterator)

                if c is None:
                    return False

                pushback.append(c)

                if not isinstance(c, Token):
                    return False
                elif not isinstance(c, (Letter, Space, Other)):
                    return False
                if c.ch!=letter:
                    return False

            return True

        if _inner():
            logger.debug("%s:  -- string found: %s",
                    self,
                    s)

            return True
        else:
           logger.debug("%s:  -- string not found: %s",
                    self,
                    s)

           self.push(pushback)
           return False

    def __repr__(self):
        result = f'[tok;ls={self.line_status};s={self.source.name}'

        if self.location is not None:
           result += f';l={self.location.line};c={self.location.column}'

        result += ']'

        return result
