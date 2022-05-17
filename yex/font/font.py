import yex.value
import yex.filename
import logging

logger = logging.getLogger('yex.general')

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
            name = None,
            doc = None,
            ):

        if doc is not None:
            self.hyphenchar = doc[r'\defaulthyphenchar']
            self.skewchar = doc[r'\defaultskewchar']
        else:
            self.hyphenchar = ord('-')
            self.skewchar = -1

        self.used = set()
        self.name = name

    def __getitem__(self, v):
        """
        If v is a string of length 1, returns the details of that character.
        If v is an integer, returns font dimension number "v"--
            that is, font[v] is equivalent to font.metrics.dimens[v],
            except that unknown "v" gets 0pt rather than KeyError.

        You may wonder why font[int] doesn't return the character with
        codepoint "int". It's because Document looks up information by
        subscripting-- so, for example, s['_font;1'] means dimension 1
        of the current font. It would make no sense for this to retrieve
        the character details, because there's no TeX type which would
        represent that. But fetching the metrics is very useful-- for
        example, for Fontdimen.
        """

        if isinstance(v, int):
            return self.metrics.dimens.get(v, yex.value.Dimen())
        elif isinstance(v, str):
            return Character(self, ord(v))
        else:
            raise TypeError()

    def __setitem__(self, n, v):
        if not isinstance(n, int):
            raise TypeError()
        if n<=0:
            raise ValueError()
        if not isinstance(v, yex.value.Dimen):
            raise TypeError()

        if n not in self.metrics.dimens and self.used:
            raise yex.exception.YexError(
                    "You can only add new dimens to a font "
                    "before you use it.")

        logger.debug(
                r"%s: set dimen %s, = %s",
                self, n, v)
        self.metrics.dimens[n] = v

    def __repr__(self):
        try:
            result = self.identifier
            if self.scale is not None:
                result += f' at {self.scale}pt'
        except AttributeError:
            result = '[unknown font]'

        return result

    @property
    def identifier(self):
        return fr'\{self.name}'

class Character:
    def __init__(self, font, code):
        self.font = font
        self.font.used.add(code)

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

def get_font_from_tokens(
        tokens,
        doc = None,
        ):
    """
    Given an Expander, finds a font with that name.

    We return an object of the relevant subclass of yex.font.Font.

    Args:
        tokens (`Expander`): an Expander positioned just before the
            specification of a font.
        doc (`Document`): use this document for getting the default
            skewchar and hyphenchar. If this is None, hyphenchar
            is a hyphen, and there is no skewchar.

    Returns:
        `Font`

    Raises:
        `ValueError`: if there is no font with the given name, or if
            the named file isn't a font.

        `YexError`: if the next tokens in the expander don't specify a font,
            including when we're at EOF.
    """

    filename = yex.filename.Filename(
            name = tokens,
            filetype = 'font',
            )

    logger.debug(r"get_font_from_tokens: the filename is: %s",
            filename)

    font = get_font_from_name(filename, doc)

    logger.debug(r"   -- giving us the font: %s",
            font)

    tokens.eat_optional_spaces()
    if tokens.optional_string("at"):
        tokens.eat_optional_spaces()
        font.scale = yex.value.Dimen(tokens)
        logger.debug(r"  -- scale is: %s",
                font.scale)
    elif tokens.optional_string("scaled"):
        tokens.eat_optional_spaces()
        font.scale = yex.value.Number(tokens)
        logger.debug(r"  -- scale is: %s",
                font.scale)
    else:
        font.scale = None
        logger.debug(r"  -- scale is not specified")

    return font

def get_font_from_name(
        name,
        doc = None,
        ):
    """
    Given a name, finds a font with that name.

    We return an object of the relevant subclass of yex.font.Font.

    Args:
        name (`str` or `Filename` or `None`): the name of the font.
            For example, `"/usr/fonts/cmr10.tfm"` or `"cmr10"`.
            `None` will get you the default font (`yex.font.Default`)
            whose metrics are hard-coded.
        doc (`Document`): use this document for getting the default
            skewchar and hyphenchar. If this is None, hyphenchar
            is a hyphen, and there is no skewchar.

    Returns:
        `Font`

    Raises:
        `ValueError`: if there is no font with the given name, or if
            the named file isn't a font.
    """

    if name is None:
        from yex.font.default import Default

        logger.debug(
                "get_font_from_name: returning default font")
        return Default()

    if isinstance(name, str):
        logger.debug(
                "get_font_from_name: Looking up %s",
                name)
        name = yex.filename.Filename(
            name = name,
            filetype = 'font',
            )

    name.resolve()

    logger.debug(
            "get_font_from_name: found %s, of type %s",
            name.path, name.filetype)

    # For now, we hard-code this.

    if name.filetype=='tfm':
        from yex.font.tfm import Tfm

        with open(name.path, 'rb') as f:
            return Tfm(
                    filename = name,
                    )
    else:
        raise ValueError("Unknown font type: %s", name.filetype)
