import yex.logging
import enum
import string
import yex.exception
import yex.util
from yex.parse.source import *
from yex.parse.token import *
from yex.parse.tokeniser import *
from typing import (
        Self, Union, TextIO, List, Type,
        TypedDict, Callable, Unpack
        )
import functools

logger = yex.logging.getLogger('parser')
position_logger = yex.logging.position_logger

@functools.total_ordering
class _CaselessEnum(enum.Enum):
    """
    An enum where the constructor can take a case-insensitive string
    giving the name of the value, as well as an integer.

    Such enums are totally ordered by the integer value of the elements.
    """
    @classmethod
    def normalise(cls, s):
        if isinstance(s, cls):
            return s
        elif isinstance(s, str):
            s = s.upper()
            if s in cls.__members__:
                return cls[s]
            else:
                names = sorted([repr(m.lower()) for m in cls.__members__])
                raise ValueError(
                        f'Values of type {cls.__name__} must be '
                        f'one of: {", ".join(names)};\n'
                        f'you gave {repr(s)}.')

        elif isinstance(s, int):
            return cls(s)
        else:
            raise TypeError(
                    f'Expected a value of type {cls.__name__}; '
                    f'you gave {s.__class__.__name__}.'
                    )

    def __eq__(self, other):
        return self.value == self.normalise(other).value

    def __ge__(self, other):
        return self.value >= self.normalise(other).value

class RunLevel(_CaselessEnum):
    "Levels you can run a parser at."

    DEEP = 10
    r"""
    Direct access to the source beneath.
    For example, this will emit group delimiters
    rather than using them to start or end groups.
    This can only be used with `next()`, rather than
    with iterators, and you probably don't want to use it.
    """

    READING = 20
    r"""
    The parser will handle most kinds of
    token for you. But it will emit all control tokens,
    whether expandable or unexpandable, as well as
    all active tokens, and all `LETTER`s and `OTHER`s.
    This is the lowest level in common use.
    """

    EXPANDING = 30
    r"""
    Like `READING`, except that the parser will
    only return control tokens for unexpandable controls.
    It will run any expandable controls for you.
    For example, you won't see any of the symbols
    between `\iffalse` and `\fi`, and you won't see any
    user-defined macros.
    """

    EXECUTING = 40
    r"""
    Like `EXPANDING`, except that unexpandable controls
    and active tokens will be run rather than emitted.
    If the result is another such item, that will be run too,
    and so on. When the parser ends up with something else, it
    will emit that.
    """

    QUERYING = 41
    r"""
    Like `EXECUTING`, except that items with a value
    will be returned rather than executed.
    The item itself is returned, not its value.
    """

class OnEof(_CaselessEnum):
    """
    What to do when we reach the end of the file.
    """

    NONE = 0
    "Return `None` forever."

    RAISE = 1
    "Raise `UnexpectedEOFError`."

    EXHAUST = 2
    "Exhaust the iterator."

class Bounding(_CaselessEnum):
    "How far to run a parser before we stop."

    NO = 0
    "Iteration ends when the source ends."

    SINGLE = 1
    """
    Iteration ends after a single character, or after a balanced group
    if the next character is a `BEGINNING_GROUP`.
    """

    BALANCED = 2
    "Same as `SINGLE`, except that a `BEGINNING_GROUP` is *required*."

    STEP = 3
    """
    Iteration ends after handling one instruction, whether or not
    it produced anything. If the instruction didn't produce anything,
    `next() `returns `None`.
    """

class Parser:

    r"""Interprets a TeX file, and expands its macros.

    Takes a source, and iterates over it,
    returning the tokens with the macros expanded
    according to the definitions
    stored in the Document attached to that source.

    By default, Parser will keep returning `None` forever,
    which is what you want if you're planning to do
    lookahead. If you're going to put this Parser into
    a `for` loop, you'll want to set `on_eof=OnEof.EXHAUST`.

    It's fine to attach another Parser to the
    same source, and to run it even when this
    one is active.

    Attributes:
        source (Union[yex.parse.Tokeniser, TextIO, List, str]: the source
        doc (yex.Document): the document we're helping create.
        bounded (Bounding): how far to run an Expander before we stop.
            If this is "balanced" or "single", it requires `on_eof="exhaust"`..
        on_eof (OnEof): what to do if we reach the end of the file.
        no_outer (bool): if True, attempting to call a macro which
            was defined as "outer" will cause an error.
            Defaults to False.
        location (Union[yex.parse.Location, None]):
            the current position of this expander,
            or None if we're not tracking a position.
        delegate (Union[yex.parse.Expander, None]):
            if this is not `None`, then when `next()`
            is called, it will return the next value from this
            Expander. When the Expander is exhausted, the field will
            be reset to None. The delegate should have
            `on_eof=OnEof.EXHAUST`
            unless you're into heavy wizardry and pain.
        running (bool): True if we're still running; False if
            we've reached the end of the part we're looking at.
        is_expanding (bool): whether this Expander is currently
            expanding tokens.

            If the runlevel is below EXPANDING, we are never expanding.
            If it's EXPANDING or higher, then we are expanding iff we
            are not forbidden to expand by a conditional.

            For example, even if level was EXPANDING, we wouldn't be expanding
            straight after `\iffalse`.
    """

    SPIN_LIMIT = 1000
    """
    Maximum number of times we can allow a parser to return
    `None` before we give up on it.
    """

    LEVEL_AS_INTEGER = None

    def __init__(self,
                 source,
                 basis: Self = None,
                 bounded = Bounding.NO,
                 on_eof = OnEof.NONE,
                 no_outer = False,
                 ):

        if self.__class__==Parser:
            raise TypeError(
                    "To create a parser, you must instantiate a subclass "
                    "of Parser."
                    )

        self.bounded = Bounding.normalise(bounded)
        self.on_eof  = OnEof.normalise(on_eof)
        self.running = True

        if self.bounded in (Bounding.SINGLE, Bounding.BALANCED) and self.on_eof!=OnEof.EXHAUST:
            raise ValueError(
                    'if bounded is "single" or "balanced", on_eof must be "exhaust"')

        self.no_outer       = no_outer

        self._bounded_limit = None
        self._delegate      = None

        if not hasattr(source, 'doc'):
            raise TypeError(
                    "source must be something which can supply a Document, "
                    f"such as a Tokeniser. You gave {source}, "
                    f"which is a {type(source)}.\n\n"
                    "You might like to look into using doc.open()."
                    )
        self.source = source

        # For convenience, we allow direct access to some of
        # Tokeniser's methods.
        for name in [
                'eat_optional_char',
                'optional_string',
                'error_position',
                'exhaust_at_eol',
                ]:
            setattr(self, name, getattr(self.source, name))

        position_logger.source = self.source.source

        logger.debug("%s: ready; called from %s",
                self,
                yex.util.show_caller,
                )

    def __iter__(self):

        spun_on_none = 0

        while self.running:

            try:
                result = self.next()
            except StopIteration:
                return

            if result is None:
                spun_on_none += 1

                if spun_on_none > self.SPIN_LIMIT:
                    raise yex.exception.SpinOnNoneError(
                            spins = spun_on_none,
                            )
            else:
                spun_on_none = 0

            yield result

    def another(self,
                level = None,
                preserve_step_bounding = False,
                **kwargs,
                ) -> Self:
        """
        Returns a parser like this one, with given changes to its behaviour.

        The result will be a parser on the same Tokeniser.
        If there are no changes requested, or if the changes requested
        make no difference, the result will be this same Parser;
        otherwise it will be a new Parser.

        Any setting specified in `kwargs` will be honoured,
        with the exception of `bounded` -- see below about that.
        All other settings will be copied from this Parser.

        How `bounded` works:
            - If `bounded` is specified in kwargs, the new parser
              will have the specified value.
            - Otherwise, if preserve_step_bounding is True, and
              `self.bounded=="step"`, the new parser will also
              have `bounded="step"`.
            - Otherwise, the new parser will always have `bounded="no"`.
        """

        if level is None:
            if self.__class__==Parser:
                level = Expanding
            else:
                level = self.__class__
        elif isinstance(level, type(Parser)):
            pass
        else:
            # Convert it here, for normalisation
            try:
                level = self._LEVELS[str(level).lower()]
            except KeyError:
                raise KeyError(
                        f"'{level}' is not a valid parser level.")

        our_params = self.params
        new_params = our_params | kwargs

        if 'bounded' not in kwargs:
            if self.bounded==Bounding.STEP and preserve_step_bounding:
                pass
            else:
                new_params['bounded'] = Bounding.NO

        if not isinstance(new_params['source'], yex.parse.Tokeniser):
            new_params['source'] = yex.parse.Tokeniser(
                    doc = self.doc,
                    source = yex.parse.Source.from_value(
                        v=new_params['source'],
                        ),
                    )

        if our_params==new_params and level==self.__class__:
            result = self
        else:
            result = level.create(
                    level = level,
                    **new_params,
                    )

        return result

    def next(self,
            **kwargs,
            ) -> Any:
        r"""
        Returns the next item.

        This is just like next() on an iterator, but with more options.
        (And indeed, our iterators are implemented in terms of this method.)

        Args are as for another().

        Raises:
            UnexpectedEOFError: on unexpected end of file, or if
                `no_outer` finds the appropriate problem.
        """

        parser = self._source_for_next.another(
                # preserve_step_bounding = True,
                **kwargs)

        """
        if kwargs=={'level': 'querying'}:
            raise ValueError()
        """

        result = parser._next_at_this_level()

        self._check_token_can_be_returned(result)

        logger.debug("%s:     -- found %s",
                self, result)

        if self.bounded==Bounding.STEP:
            pass
        elif self.bounded!=Bounding.NO and self._bounded_limit is None:
            # This must be the first next() since we started.
            # Let's see whether we've been given a single item.

            if isinstance(result, BeginningGroup):
                # we need to read a balanced pair.
                self._bounded_limit = self.source.pushback.group_depth

                logger.debug(
                        "%s:        -- opens bounded expansion, read again",
                        self)
                result = self.next()
            elif self.bounded=='balanced':
                # First result wasn't a BeginningGroup,
                # but it should have been.
                raise yex.exception.NeededBalancedGroupError(
                        problem=result)
            else:
                # First result wasn't a BeginningGroup,
                # so we handle it and then stop.
                logger.debug("%s:  -- the only symbol in a bounded expansion",
                        self)
                self.running = False

        if self._bounded_limit is not None:
            if self.source.pushback.group_depth < self._bounded_limit:
                logger.debug(
                        ('%s: end of bounded expansion: group depth is %s, '
                        'which is below the starting limit, %s'
                            ),
                        self, self.source.pushback.group_depth,
                        self._bounded_limit,
                        )
                self.running = False
                result = None

        if result is None:

            if self._delegate is not None:
                logger.debug(
                        ('%s: delegate %s is all done; '
                        'carrying on with our own stuff'),
                        self, self._delegate,
                        )
                self._delegate = None
                return self.next(**kwargs)

            elif parser.bounded==Bounding.STEP:
                return None

            elif parser.on_eof==OnEof.RAISE:
                logger.debug("%s: unexpected EOF", self)
                raise yex.exception.UnexpectedEOFError()

            elif parser.on_eof==OnEof.EXHAUST:
                raise StopIteration

        return result

    def _next_via_delegate(self, **kwargs) -> Any:

        assert self._delegate is not None

        logger.debug("%s: delegating to %s, with kwargs %s",
                self, self._delegate, kwargs)

        result = self._delegate.next(**kwargs)

        if result is None:
            logger.debug("%s: delegate %s is exhausted",
                    self, self._delegate)
            self._delegate = None
            return self.next(**kwargs)

        return result

    def _check_token_can_be_returned(self, token):
        pass

    @property
    def _source_for_next(self) -> Self:
        r"""
        Where we're getting the next item from.

        That's self.delegate if it's set. Otherwise, it's ourselves.

        A delegate may have a delegate of its own, but that makes no
        difference to us.

        This only applies to level==RunLevel.QUERYING or RunLevel.EXECUTING,
        and to our next() method itself. Other levels get their items
        directly from the source.
        """
        if self._delegate is not None:
            logger.debug("%s: delegating to %s",
                    self, self._delegate)

            return self._delegate
        else:
            return self

    def _next_at_this_level(self) -> Any:
        raise NotImplementedError()

    def _notice_item(self, item:Any) -> None:
        r"""
        Logs an item to \tracingcommands.

        Don't optimise this out: subclasses need to override it.

        Args:
            item: whatever you want to log
        """
        self.doc.notice_item(
                item=item,
                )

    def peek(self) -> Any:
        """
        Returns the item which is next due to be returned by `next()`.
        If this would go past the end of the file, we return `None`,
        whatever the setting of `on_eof`.
        """
        result = self.next(
                on_eof = OnEof.NONE,
                )
        self.source.pushback.push(result)
        return result

    @property
    def location(self) -> Union['yex.parse.Location', None]:
        if self.running:
            return self.source.location
        else:
            return None

    @location.setter
    def location(self, v: 'yex.parse.Location'):
        logger.debug("%s: set location: %s",
                self,
                v
                )
        if self.running:
            self.source.location = v
        else:
            raise ValueError("can't set location without a source")

    @property
    def is_expanding(self) -> bool:
        return False

    def push(self,
             thing: Any,
             clean_char_tokens: bool = False,
             is_result:bool = False,
            ):
        r"""
        Pushes back a token, a character, or anything else.

        This is mostly just a wrapper for the `push` method in
        `Tokeniser`. But we do check for "beginning group"
        and "ending group" tokens, and adjust our fields accordingly.

        All Parsers share pushback, and in general it's fine to push
        things through a parser when you received them from a
        different Parser. The only exception to this is when
        you're using balanced expansion: because we have to keep a count of
        balanced braces, you should remember to push Tokens back
        through the Parser that gave you them.

        If you push bare characters, they will be converted by the
        source as it thinks appropriate.

        Args:
            thing: whatever you're pushing back.
                Pushing None will be ignored.
                If this is a string, or a list specifically, it
                will be split into its members and pushed in reverse order.
                For example, pushing 'cat' is the same as pushing 't',
                then pushing 'a', then pushing 'c'.

            clean_char_tokens: if True, all bare characters
                will be converted to the Tokens for those characters.s
                (For example, 'T', 'e', 'X' -> ('T' 12) ('e' 12) ('X' 12).)
                The rules about how this is done are on p213 of the TeXbook.
                If False, the characters will remain bare characters
                and the source will tokenise them as usual when it
                gets to them.

            is_result: If you're a control, and your job involves
                reading some data, then pushing a result, set this to True
                when you push the result. This will allow \expandafter
                to work correctly.

                If you're implemented through a decorator, and your result
                is pushed via returning it, you don't have to worry:
                the decorator will set is_result=True when it pushes your
                return values.

        Raises:
            EOFError: if this parser is exhausted.
            GoneBeforeTheBeginningError: if we're bounded, and you push more
                BEGINNING_GROUP tokens than you've already received.
        """

        if not self.running:
            raise EOFError()

        if not isinstance(thing, (str, list)):
            thing = [thing]

        if clean_char_tokens:

            def _clean(c):
                if isinstance(c, str):
                    return Token.get(
                            ch=c,
                            location=self.source.location,
                            )
                else:
                    return c

            thing = [_clean(c) for c in thing]

        self.source.pushback.push(thing,
                                  is_result = is_result,
                                  )

        if self._bounded_limit is not None:
            if self.source.pushback.group_depth < self._bounded_limit:
                logger.debug(
                        '%s: group_depth is %d, but bounded_limit is %d',
                        self, self.pushback.group_depth,
                        self._bounded_limit)
                raise yex.exception.GoneBeforeTheBeginningError()

    def eat_optional_spaces(self,
                            level:RunLevel=RunLevel.DEEP,
                            ) -> List[Token]:
        """
        Eats zero or more space tokens.

        This is like Tokeniser.eat_optional_spaces(), except that it can
        also execute controls and active characters, then continue to
        consider the result.

        Returns a list of the Tokens consumed.

        Args:
            level: the runlevel to run at.
        """
        level = RunLevel.normalise(level)

        if level==RunLevel.DEEP:
            return self.source.eat_optional_spaces()

        result = []
        while True:
            result.extend(self.source.eat_optional_spaces())

            t = self.next(level=RunLevel.QUERYING, on_eof=OnEof.NONE)

            if t is None:
                return result
            elif isinstance(t, Token) and t.ch in string.whitespace:
                result.append(t.ch)
            elif isinstance(t, str) and t in string.whitespace:
                result.append(t)
            else:
                self.push(t)
                return result

    def get_digit_sequence(self,
                           accept_ch:str,
                           accept_decimal_point:bool,
                           ) -> str:
        r"""
        Reads and returns a series of symbols.

        The result is taken from the next zero or more items.
        They are accepted if:

        - they are LETTER or OTHER tokens, and their "ch" property is
                in `accept_ch`; or
        - they are single-character strings, and they are in `accept_ch`.

        This exists because if we read in the indexes of arrays using
        any other method, we risk `\catcodeNN=` affecting the way the symbol
        *after* the value which is assigned to `\catcode`NN.
        See `test_tokeniser_whitespace_after_control_words()`.

        Tokens are represented in the result by their `ch` property.
        Strings are used directly.

        Args:
            accept_ch: the characters we can accept
            accept_decimal_point: if `True`, act as though `'.,'` were
                included in accept_ch, except that they can only
                be matched once.

        Returns:
        """

        DECIMAL_POINTS = '.,'
        original_accept_ch = accept_ch

        if accept_decimal_point:
            accept_ch += DECIMAL_POINTS

        logger.debug("%s: get_digit_sequence begins; accepting %s",
                self, accept_ch)

        result = ''
        exp = self.another(level=Expanding, on_eof=OnEof.NONE)

        while True:
            item = exp.next()

            if isinstance(item, (Letter, Other)) and item.ch in accept_ch:
                addendum = item.ch
                logger.debug("%s:   -- accepted token, so: %s", self, repr(result))
            elif (isinstance(item, str) and
                    len(item)==1 and
                    item in accept_ch):
                addendum = item
                logger.debug("%s:   -- accepted char, so: %s", self, repr(result))
            else:
                if isinstance(item, Space):
                    logger.debug("%s:   -- ending on %s, so result is: %s",
                            self, repr(item), repr(result))
                else:
                    logger.debug((
                        "%s:   -- ending on %s (will push), "
                        "so result is: %s"),
                                 self, repr(item), repr(result))
                    self.push(item)

                return result

            result += addendum
            if addendum in DECIMAL_POINTS:
                accept_ch = original_accept_ch

    @property
    def delegate(self) -> Union[Self, None]:
        return self._delegate

    @delegate.setter
    def delegate(self, value:Union[Self, None]):
        """
        Raises:
            MultipleDelegatesError: if value is not None and we already
                have a delegate.
        """
        if self._delegate is not None:
            raise yex.exception.MultipleDelegatesError()

        self._delegate = value

    def end(self) -> None:
        """
        Marks this Parser as finished.
        """
        logger.debug(r'%s: we have reached an \end', self)
        self.source.pushback.clear()
        self.running = False

    @property
    def doc(self) -> 'yex.Document':
        return self.source.doc

    @property
    def params(self) -> dict:
        result = dict([
                (name, getattr(self, name))
                for name in [
                    'source',
                    'bounded',
                    'on_eof',
                    'no_outer',
                    ]
                ])
        return result

    @classmethod
    def create(cls,
               level='executing',
               **kwargs):

        if isinstance(level, str):
            subclass = cls._LEVELS[level.lower()]
        else:
            assert issubclass(level, Parser), level
            subclass = level

        result = subclass(
                **kwargs,
                )

        return result

    """
    @classmethod
    def create(cls,
               another: Self = None,
               force_creation: bool = False,
               **kwargs):
    """

    """
    if (
            'source' in kwargs and
            not isinstance(kwargs['source'], yex.parse.Tokeniser)
            ):

        kwargs['source'] = yex.parse.Tokeniser(
                doc = self.doc,
                source = yex.parse.Source.from_value(
                    v=kwargs['source'],
                    ),
                )
                """

    """
    if 'level' in kwargs:
        if hasattr(kwargs['level'], 'name'):
            kwargs['level'] = kwargs['level'].name.lower()
        try:
            subclass = cls._LEVELS[kwargs['level']]
        except KeyError:
            raise ValueError(kwargs['level'])
    else:
        subclass = cls

    if subclass==Parser:
        subclass = Executing # the default kind of Parser

    if another is None:
        new_params = kwargs
    else:
        another_params = another.params
        new_params = another_params | kwargs

        if (
                another_params == new_params and
                another.__class__ == subclass and
                not force_creation):
            return another

    """
    """
    if 'bounded' not in kwargs:
        if self.bounded==Bounding.STEP and preserve_step_bounding:
            pass
        else:
            new_params['bounded'] = Bounding.NO
        """

    """
    result = subclass(**new_params)
    return result
    """

    def __repr__(self):
        result = '[%s.%04x;' % (
                self.__class__.__name__,
                id(self) % 0xFFFF,
                )
        if self.bounded==Bounding.NO:
            pass
        elif self.bounded==Bounding.STEP:
            result += 'step;'
        elif self._bounded_limit is None:
            result += 'bounded;'
        else:
            result += 'bounded=%d;' % (self._bounded_limit)

        if self.on_eof in [OnEof.RAISE, OnEof.EXHAUST]:
            result += str(self.on_eof)+';'

        if self.no_outer:
            result += 'no_outer;'

        result += repr(self.source)[5:-1]
        result += ']'
        return result

class Deep(Parser):

    LEVEL_AS_INTEGER = 10

    def _next_at_this_level(self) -> Any:

        if not self.running:
            return None

        while True:
            result = next(self.source)

            if isinstance(result, yex.parse.Internal):
                result(self)
            elif self.bounded==Bounding.STEP:
                if result is None:
                    return None
                else:
                    logger.debug("%s:  stopping for stepping", self)
                    break
            else:
                break

        if self.no_outer and isinstance(result, yex.parse.ControlName):

            # We have to enforce no_outer.

            try:
                referent = self.doc.get_control(
                        result.identifier,
                        )

                if getattr(referent, 'is_outer', False):
                    logger.debug("%s: -- which -> %s, which is outer",
                            self, referent)
                    raise yex.exception.OuterOutOfPlaceError(
                            problem = result.identifier,
                            )
            except KeyError:
                pass

        return result

class Reading(Parser):

    LEVEL_AS_INTEGER = 20

    def _next_at_this_level(self) -> Any:
        while True:
            if self._bounded_limit is not None and self.running:
                if self.source.pushback.group_depth < self._bounded_limit:
                    self.running = False
                    logger.debug("%s: end of bounded expansion", self)

            if not self.running:
                raise StopIteration()

            token = next(self.source)

            logger.debug("%s: token: %s",
                    self,
                    token,
                    )

            if not hasattr(token, 'category'):

                # Not a token. Could be a ControlName, could be some
                # other class, could be None. Anyway, it's not our problem;
                # pass it through.

                if token is None and self.bounded==Bounding.STEP:
                    raise StopIteration()
                elif self.doc.ifdepth[-1]:

                    if getattr(token, 'is_array', False):
                        logger.debug(
                            "%s  -- not a token: %s; looking up index",
                                self, token,)

                        token = token.get_element_from_parser(self)
                        logger.debug("%s  -- found: %s; passing through",
                                self, token,)
                        self.source.eat_whitespace_after_control()

                    else:
                        logger.debug("%s  -- not a token; "
                                "passing through: %s",
                                self, token,)

                    return token
                else:
                    logger.debug("%s  -- not passing %s because "
                            "of a conditional",
                            self, token)

                    continue

            if isinstance(token, (
                yex.parse.token.ControlName,
                yex.parse.token.Active,
                )):

                name = token.identifier

                try:
                    handler = self.doc.get_control(name)
                except KeyError:
                    if self.doc.ifdepth[-1]:
                        logger.debug(
                                "%s: %s is undefined; returning it",
                                self, token)
                        return token
                    else:
                        logger.debug(
                                "%s: %s is undefined; not returning it "
                                "because of a conditional",
                                self, token)
                    continue

                if (isinstance(self, Expanding) and
                    handler.is_array and
                    self.doc.ifdepth[-1]):

                    logger.debug((
                        "%s: found control %s (which is a %s) "
                        "and it's an array; looking up an element"),
                        self, handler, type(handler))

                    index = yex.value.Value.get_value_from_parser(self)

                    logger.debug("%s:   -- element %s",
                        self, index)

                    handler = handler.get_element(index=index)

                    logger.debug("%s:   -- element %s found: %s",
                        self, index, handler)
                    self.source.eat_whitespace_after_control()

                if not isinstance(handler, yex.control.Expandable):
                    if self.doc.ifdepth[-1]:
                        logger.debug(
                                '%s: %s is unexpandable; returning it',
                                self, handler)
                        return handler
                    else:
                        logger.debug(
                                '%s: %s is unexpandable; not returning it '
                                'because of a conditional',
                                self, handler)
                        continue

                elif self.no_outer and getattr(handler, "is_outer", False):
                    raise yex.exception.OuterOutOfPlaceError(
                            problem = handler.identifier,
                            )

                elif (not isinstance(self, Expanding) and
                      not handler.even_if_not_expanding):

                    # don't refactor this into the other "not expanding";
                    # if it's a control or active character, we must
                    # raise an error if it's "outer", even if we're
                    # not expanding.
                    logger.debug(
                            "%s: we're not expanding; returning control: %s",
                            self, handler)
                    return handler

                elif self.doc.ifdepth[-1] or \
                        handler.conditional or \
                        handler.even_if_not_expanding:

                    # We're not prevented from executing by \if.
                    #
                    # (Or, this is one of the even_if_not_expanding controls,
                    # whose contents don't get expanded; in cases like that
                    # we have to execute but tell the control not
                    # to do anything, or the parser gets confused.
                    # See p215 of the TeXbook, and
                    # test_register_table_name_in_message().)

                    self._notice_item(item=handler)

                    logger.debug("%s: calling %s",
                            self, handler)

                    # control exists, so run it.

                    with position_logger.report(token):
                        received = handler(
                                parser = self.another(
                                    on_eof=OnEof.NONE),
                                )

                    logger.debug("%s: finished calling %s (%s)",
                            self, handler, type(handler))

                    if received is not None:
                        logger.debug('%s:   -- received: %s',
                                self, received)
                        return received

                else:
                    logger.debug("%s: not executing %s because "+\
                            "we're inside a conditional block",
                            self,
                            handler,
                            )

            elif isinstance(token, Internal):
                logger.debug("%s:  -- running internal token: %s",
                        self,
                        token,
                        )
                token(self)

            elif not isinstance(self, Expanding):
                logger.debug(
                        "%s: we're not expanding; returning %s",
                        self,
                        token,
                        )
                return token

            elif self.doc.ifdepth[-1]:
                logger.debug("%s:  -- returning: %s",
                        self,
                        token,
                        )
                return token
            else:
                logger.debug(
                        "%s:  -- dropping because of conditional: %s",
                        self,
                        token,
                        )

            if self.bounded==Bounding.STEP:
                logger.debug("%s:  stopping for stepping", self)
                return None

class Expanding(Reading):
    LEVEL_AS_INTEGER = 30

    @property
    def is_expanding(self) -> bool:
        return self.doc.ifdepth[-1]

    def _check_token_can_be_returned(self, token):
        assert not isinstance(token, yex.keyword.Array), (
                        "next() was passed an Array; it should have "
                        "already been dereferenced to a Register."
                        )

class Executing(Expanding):
    LEVEL_AS_INTEGER = 40

    def _next_at_this_level(self) -> Any:

        while True:
            name = None
            item = super()._next_at_this_level()
            logger.debug(
                    "%s: considering %s for executing or querying",
                    self, item)

            if isinstance(item, yex.parse.ControlName):
                try:
                    v = self.doc[item.identifier]
                    logger.debug(
                            "%s:     -- ==%s (%s)",
                            self, v, type(v))
                    name = item
                    item = v
                except KeyError:
                    pass # just use the unexpanded control then

            if isinstance(item, yex.control.Control):

                if not isinstance(self, Querying) and item.is_queryable:
                    # "item" here is the array element we found if the
                    # original item was an array. Otherwise it's the
                    # original item itself.

                    logger.debug("%s:     -- a queryable control", self)

                    with position_logger.report(item):
                        result = item.query(parser=self)

                    logger.debug("%s:  -- == %s (%s); returning that",
                            self, result, type(result))
                    return result

                else:

                    logger.debug("%s:     -- an executable control", self)

                    self._notice_item(item=item)

                    with position_logger.report(item):
                        try:
                            received = item(
                                    parser = self.another(
                                        on_eof=OnEof.NONE),
                                    )
                        except yex.exception.YexError as ye:
                            logger.debug("%s:       -- it raised %s",
                                    self, ye.__class__.__name__)
                            if isinstance(self, Querying):
                                # there's a possibility of confusion
                                ye.mark_as_possible_rvalue(item)
                            raise

                if received is not None:
                    logger.debug(
                            '%s:   -- received: %s; returning that directly',
                            self, received)
                    return received

                logger.debug("%s: done calling %s",
                        self, item)

            elif self.doc.ifdepth[-1]:
                logger.debug("%s:     -- not a control; returning it", self)
                return item

            else:
                logger.debug((
                    "%s:     -- not a control; not returning it, "
                    "because we're in a False conditional"), self)

            if self.bounded==Bounding.STEP:
                if not self.doc.ifdepth[-1]:
                    logger.debug((
                        "%s:  not stopping for stepping, "
                        "because we're in a False conditional"
                            ), self)
                elif getattr(item, 'conditional', False):
                    logger.debug((
                            "%s:  not stopping for stepping, ",
                            "because we only saw a conditional",
                            ), self)
                else:
                    logger.debug("%s:  stopping for stepping", self)
                    return None

            # and round we go again

class Querying(Executing):
    LEVEL_AS_INTEGER = 41

Parser._LEVELS = dict([
    (p.__name__.lower(), p)
    for p in [
        Deep,
        Reading,
        Expanding,
        Executing,
        Querying,
        ]])
