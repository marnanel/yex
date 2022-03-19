import mex.value
import mex.filename
import logging

commands_logger = logging.getLogger('mex.commands')

class Font:

    DIMEN_SLANT_PER_PT = 1
    DIMEN_INTERWORD_SPACE = 2
    DIMEN_INTERWORD_STRETCH = 3
    DIMEN_INTERWORD_SHRINK = 4
    DIMEN_X_HEIGHT = 5
    DIMEN_QUAD_WIDTH = 6
    DIMEN_EXTRA_SPACE = 7

    # σ-params
    DIMEN_QUAD = 6
    DIMEN_NUM1 = 8
    DIMEN_NUM2 = 9
    DIMEN_NUM3 = 10
    DIMEN_DENOM1 = 11
    DIMEN_DENOM2 = 12
    DIMEN_SUP1 = 13
    DIMEN_SUP2 = 14
    DIMEN_SUP3 = 15
    DIMEN_SUB1 = 16
    DIMEN_SUB2 = 17
    DIMEN_SUP_DROP = 18
    DIMEN_SUB_DROP = 19
    DIMEN_DELIM1 = 20
    DIMEN_DELIM2 = 21
    DIMEN_AXIS_HEIGHT = 22

    # ξ-params
    DIMEN_DEFAULT_RULE_THICKNESS = 8
    DIMEN_BIG_OP_SPACING1 = 9
    DIMEN_BIG_OP_SPACING2 = 10
    DIMEN_BIG_OP_SPACING3 = 11
    DIMEN_BIG_OP_SPACING4 = 12
    DIMEN_BIG_OP_SPACING5 = 13

    def __init__(self,
            tokens = None,
            filename = None,
            scale = None,
            name = None,
            state = None,
            ):

        if state is not None:
            self.hyphenchar = state['defaulthyphenchar']
            self.skewchar = state['defaultskewchar']
        else:
            self.hyphenchar = ord('-')
            self.skewchar = -1

        self._metrics = None
        self.has_been_used = False

    def __getitem__(self, v):
        """
        If v is a string of length 1, returns the details of that character.
        If v is an integer, returns font dimension number "v"--
            that is, font[v] is equivalent to font.metrics.dimens[v],
            except that unknown "v" gets 0pt rather than KeyError.

        You may wonder why font[int] doesn't return the character with
        codepoint "int". It's because State looks up information by
        subscripting-- so, for example, s['_font;1'] means dimension 1
        of the current font. It would make no sense for this to retrieve
        the character details, because there's no TeX type which would
        represent that. But fetching the metrics is very useful-- for
        example, for Fontdimen.
        """

        if isinstance(v, int):
            return self.metrics.dimens.get(v, mex.value.Dimen())
        elif isinstance(v, str):
            return Character(self, ord(v))
        else:
            raise TypeError()

    def __setitem__(self, n, v):
        if not isinstance(n, int):
            raise TypeError()
        if n<=0:
            raise ValueError()
        if not isinstance(v, mex.value.Dimen):
            raise TypeError()

        if n not in self.metrics.dimens and self.has_been_used:
            raise mex.exception.MexError(
                    "You can only add new dimens to a font "
                    "before you use it.")

        commands_logger.debug(
                r"%s: set dimen %s, = %s",
                self, n, v)
        self.metrics.dimens[n] = v

    def _set_from_tokens(self, tokens):
        self.filename = mex.filename.Filename(
                name = tokens,
                filetype = 'font',
                )

        commands_logger.debug(r"font is: %s",
                self.filename.value)

        tokens.eat_optional_spaces()
        if tokens.optional_string("at"):
            tokens.eat_optional_spaces()
            self.scale = mex.value.Dimen(tokens)
            commands_logger.debug(r"  -- scale is: %s",
                    self.scale)
        elif tokens.optional_string("scaled"):
            tokens.eat_optional_spaces()
            self.scale = mex.value.Number(tokens)
            commands_logger.debug(r"  -- scale is: %s",
                    self.scale)
        else:
            self.scale = None
            commands_logger.debug(r"  -- scale is not specified")

    def __repr__(self):
        result = self.name
        if self.scale is not None:
            result += f' at {self.scale}pt'

        return result

class Character:
    def __init__(self, font, code):
        self.font = font

        if isinstance(code, str):
            self.code = ord(code)
        else:
            self.code = code

    @property
    def metrics(self):
        return self.font.metrics.get_character(self.code)

    @property
    def glyph(self):
        return self.font.glyphs.chars[self.code]

    def __repr__(self):
        if self.code>=32 and self.code<=127:
            character = ' (%s)' % (chr(self.code))
        else:
            character = ''

        return '[%04x%s in %s]' % (
                self.code,
                character,
                self.font,
                )
