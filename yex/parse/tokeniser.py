import yex
import yex.logging
from yex.parse.token import *
from typing import List, TextIO, Union, Any, Generator
import string
import io

logger = yex.logging.getLogger('tokeniser')

HEX_DIGITS = string.hexdigits[:-6] # lose capitals

class Tokeniser:
    r"""
    A tokeniser takes characters from a [source](yex.parse.Source.md),
    such as a file, and produces [tokens](yex.parse.Token.md) of the
    correct categories.

    Then, an [parser](yex.parse.Parser.md) will request tokens
    from the tokeniser, and do something with them. Hopefully,
    it'll be something useful.
    """

    # Line statuses.
    # These are defined on p46 of the TeXbook.
    BEGINNING_OF_LINE = 'N'
    MIDDLE_OF_LINE = 'M'
    SKIPPING_BLANKS = 'S'

    def __init__(self,
                 doc: 'yex.Document',
                 source: Union[TextIO, List, str],
                 pushback: Union['yex.parse.Pushback', None]=None,
                 ):

        self.doc = doc
        self.catcodes = doc.controls[r'\catcode']

        self.line_status = self.BEGINNING_OF_LINE

        self.pushback = pushback
        if self.pushback is None:
            self.pushback = yex.parse.Pushback()

        source: 'yex.parse.Source'
        """
        Something which produces characters for us to use.
        """

        try:
            name = source.name
        except AttributeError:
            name = repr(source)

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

        # For convenience, we allow direct access to some of
        # the source's methods.
        for name in [
                'location',
                'exhaust_at_eol',
                ]:
            setattr(self, name, getattr(self.source, name))

        self.source.line_number_setter = (
                doc.get_control(r'\inputlineno').update
                )
        self._iterator = self._read()

        self.incoming = Incoming(
                source = _caret_eater(self.source),
                pushback = self.pushback,
                )

    def push(self, thing: Any) -> None:
        """
        Pushes something back. Next time someone reads the tokeniser,
        they will get this item-- unless someone pushes something
        else back, which will come out first.

        Args:
            thing: anything you like, which gets pushed back.
        """
        self.pushback.push(thing)

    def __iter__(self):
        return self

    def __next__(self):
        result = next(self._iterator)
        try:
            self.location = result.location
        except AttributeError:
            pass
        return result

    def _get_catcode(self, c):
        if isinstance(c, Token):
            return c.category
        elif not isinstance(c, str):
            return None
        elif len(c)==1:
            try:
                return self.catcodes.get_directly(ord(c))
            except KeyError:
                if ord(c)>127:
                    raise ValueError(
                            "The text contains a character with codepoint "
                            f"U+{ord(c):04x}. At present, yex implements the basic "
                            "TeX system, which means that all characters must "
                            "have codepoints below 128.")
        else:
            raise yex.exception.OrdLengthWasNot1Error(
                    problem = c,
                    )

    def correct_line_number(self) -> None:
        r"""
        Assigns the correct line number to \inputlineno.

        You only need to call this if you've already changed it temporarily:
        for example, by doing an \input. Otherwise, it updates automatically.
        """
        if self.source.line_number_setter is not None and \
                self.source.line_number is not None:
            self.source.line_number_setter(self.source.line_number)

    def _read(self) -> Any:
        # See p46ff of the TeXbook for this algorithm.

        logger.debug("%s: tokeniser ready",
                self)

        for c in self.incoming: # never exhausts

            if not isinstance(c, str):
                logger.debug(
                        "%s: received %s (which is %s); passing it through",
                        self, repr(c), c.__class__.__name__)

                yield c
                continue

            category = self._get_catcode(c)

            logger.debug("%s: received %s, %s",
                    self, repr(c), category)

            if category in (
                    Token.BEGINNING_GROUP,
                    Token.END_GROUP,
                    Token.MATH_SHIFT,
                    Token.ALIGNMENT_TAB,
                    Token.PARAMETER,
                    Token.SUPERSCRIPT,
                    Token.SUBSCRIPT,
                    Token.LETTER,
                    Token.OTHER,
                    Token.ACTIVE,
                    ):

                new_token = Token.get(
                    ch = c,
                    category = category,
                    location = self.source.location,
                    )

                logger.debug("%s:   -- yield %s",
                        self, new_token)

                self.pushback.adjust_group_depth(c=new_token,
                        why = 'tokenised',
                        )

                yield new_token

                self.line_status = self.MIDDLE_OF_LINE

            elif category==Token.END_OF_LINE:

                if self.line_status==self.BEGINNING_OF_LINE:
                    logger.debug("%s:   -- paragraph break",
                            self)

                    yield ControlName(
                            ch = 'par',
                            location = self.source.location,
                            )

                elif self.line_status==self.MIDDLE_OF_LINE:
                    logger.debug("%s:   -- EOL, treated as space",
                            self)

                    yield Token.get(
                            ch = chr(32),
                            category = Token.SPACE,
                            location = self.source.location,
                            )
                else:
                    logger.debug("%s:   -- ignored",
                            self)

                self.source.discard_rest_of_line()
                self.line_status = self.BEGINNING_OF_LINE

            elif category==Token.SPACE:

                if self.line_status==self.MIDDLE_OF_LINE:
                    logger.debug("%s:   -- space",
                            self)

                    yield Token.get(
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
                        self, repr(c), category)

                name = ''
                for c2 in self.incoming:
                    category2 = self._get_catcode(c2)
                    logger.debug("%s:   -- and %s, %s",
                            self, repr(c2), category2)

                    if category2 in (None, Token.END_OF_LINE) and name=='':
                        break
                    elif category2==Token.LETTER:
                        name += str(c2)
                    else:
                        break

                location = self.source.location

                if name=='':
                    try:
                        name = c2.ch
                    except AttributeError:
                        name = str(c2)
                else:
                    self.push([c2])
                    self.line_status = self.SKIPPING_BLANKS

                logger.debug("%s:     -- so the control is named %s",
                        self, name)

                new_token = ControlName(
                        ch = name,
                        location=self.source.location,
                        )

                logger.debug("%s:     -- producing %s - %s",
                        self, new_token, type(new_token))

                yield new_token

            elif category==Token.COMMENT:
                self.source.discard_rest_of_line()
                self.line_status = self.BEGINNING_OF_LINE

            elif category==Token.INVALID:
                logger.debug("%s:   -- invalid",
                        self)

                logger.warning("Invalid character found: %s",
                        repr(c))

            elif category==Token.IGNORED:
                logger.debug("%s:   -- ignored",
                        self)

            else:
                logger.debug("%s:   -- unknown!",
                        self)
                raise yex.exception.UnknownCategoryError(
                        ch = c,
                        category = category,
                        )

    def eat_whitespace_after_control(self) -> None:
        r"""
        Eats all the next tokens which disappear after a control--
        these being spaces and newlines.
        """
        while True:

            c = self.pushback.pop()
            if c is None:
                c = next(self.incoming)

            if c is None:
                return
            elif self._get_catcode(c) not in Token.DISAPPEARS_AFTER_CONTROL:
                logger.debug("%s: not whitespace, pushing back: %s",
                        self, c);
                self.push(c)
                return
            else:
                logger.debug("%s: whitespace after control; absorbing: %s",
                        self, c);

    def _single_error_position(self,
                               frame: 'yex.document.Callframe',
                               caller:str,
                               ) -> str:

        FORMAT = (
                'File "%(filename)s", line %(line)d, in %(macro)s:\n'
                '  %(code)s\n'
                '  %(indent)s^\n'
                )

        EXCERPT_WIDTH = yex.util.screen_width()-1

        if frame.location is None:
            return f'In {caller}:\n  no frame information\n'

        # FIXME This will break if they're in separate files.
        # FIXME Make Source account for that.
        try:
            line = self.source.lines[frame.location.line]
        except IndexError:
            line = '(?)'
        column_number = self.source.column_number or 0

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

    def error_position(self, message:str) -> str:

        def callee_name(index:int) -> str:
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

    def eat_optional_spaces(self) -> List[Token]:
        """
        Eats zero or more space tokens.
        This is <optional spaces> on p264 of the TeXbook.

        Returns:
            a list of the Tokens consumed.
        """
        result = []

        for token in self._iterator:
            if token is None:
                return result
            elif isinstance(token, Token) and token.is_space:
                result.append(token)
            else:
                self.push(token)
                return result

    def eat_optional_char(self, ch: str) -> Union[Token, None]:
        """
        If the next token stands for the given character, we eat and return it.
        Otherwise, no character is consumed, and we return None.

        Args:
            ch (str): the character, to check whether token.ch==ch

        Returns:
            Token, or None.
        """

        token = next(self._iterator)

        if hasattr(token, 'ch') and token.ch==ch:
            logger.debug("    -- %s: %s.ch==%s",
                    self, token, repr(ch))
            return token
        else:
            logger.debug("    -- %s: %s.ch is not %s",
                    self, token, repr(ch))
            self.push(token)
            return None

    def optional_string(self, s:str) -> bool:

        to_push = []
        c = None

        logger.debug("%s: checking for string: %s",
                self,
                repr(s))

        def _inner():
            for letter in s:
                c = next(self._iterator)

                if c is None:
                    return False

                to_push.append(c)

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
                    repr(s))

            return True
        else:
           logger.debug("%s:  -- string not found: %s",
                    self,
                    repr(s))

           self.push(to_push)
           return False

    def peek(self) -> Any:
        """
        Returns the next character to be produced by __next__(),
        but doesn't consume it. When you next call __next__(),
        or call peek() again, the result will be the same.
        """

        result = next(self)

        self.push(result)

        return result

    def __repr__(self):
        result = f'[tok;ls={self.line_status};s={self.source.name}'

        if self.location is not None:
           result += f';l={self.location.line};c={self.location.column}'

        result += ']'

        return result

class Incoming:
    r"""
    Produces a pushback's items, or the source's while it has none.
    """
    def __init__(self, source,
                 pushback: 'yex.parse.Pushback'):
        self.source = source
        self.pushback = pushback

        assert pushback is not None

    def __iter__(self):
        return self

    @property
    def location(self) -> Union['yex.parse.Location', None]:
        """
        Returns where we are in the document.

        The Pushback has priority; after that, we ask the Source.

        Returns:
            a Location, or None.
        """

        for item in reversed(self.pushback.items):
            try:
                if not hasattr(item, 'location'):
                    continue

                result = item.location

                if result is not None:
                    return result
            except AttributeError:
                continue

        return self.source.location

    def __next__(self):
        if self.pushback.items:
            result = self.pushback.pop()
            self.pushback.adjust_group_depth(
                    result,
                    why = 'on pop',
                    )
        else:
            result = next(self.source)
            self.pushback.adjust_group_depth(
                    result,
                    why = 'on read',
                    )

        return result

    def __repr__(self):
        if self.pushback.items:
            return f'[incoming;source={self.source};pb={self.pushback.items}]'
        else:
            return f'[incoming;source={self.source}]'

def _caret_eater(
        source: Generator[str, None, None],
        ) -> Generator[str, None, None]:
    """
    Replaces caret sequences in a stream of characters
    with the characters they represent.

    TeXbook:
        p45
    """

    buffer = ''

    while True:
        try:
            if buffer:
                first = buffer[0]
                buffer = buffer[1:]
            else:
                first = next(source)

            if first!='^':
                yield first
                continue

            second = next(source)
            if second!='^':
                yield first
                buffer = second + buffer
                continue

            third = next(source)

            if third in HEX_DIGITS:
                fourth = next(source)

                if fourth in HEX_DIGITS:
                    yield chr(int(third+fourth, 16))
                    continue
                else:
                    buffer = fourth + buffer
                    # and fall through

            codepoint = ord(third)

            if codepoint<64:
                yield chr(codepoint+64)
            elif codepoint<128:
                yield chr(codepoint-64)
            else:
                yield third

        except StopIteration:
            for c in buffer:
                yield c
            return
