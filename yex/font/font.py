import yex.value
import yex.filename
import logging
import appdirs
import os
import glob
import importlib.resources

logger = logging.getLogger('yex.general')

APPNAME = 'yex'

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
            f = None,
            name = None,
            filename = None,
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
        self.filename = filename

        self._custom_dimens = {}

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
            if v in self._custom_dimens:
                return self._custom_dimens[v]
            else:
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
        return self.name

    @classmethod
    def from_tokens(
            cls,
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

        filename = yex.filename.Filename.from_tokens(
                tokens = tokens,
                )

        logger.debug(r"Font.from_tokens: the filename is: %s",
                filename)

        font = cls.from_name(filename, doc)

        logger.debug(r"   -- giving us the font: %s",
                font)

        tokens.eat_optional_spaces()
        if tokens.optional_string("at"):
            tokens.eat_optional_spaces()
            font.size = yex.value.Dimen.from_tokens(tokens)
            font.scale = None
            logger.debug(r"  -- size is: %s",
                    font.size)
        elif tokens.optional_string("scaled"):
            tokens.eat_optional_spaces()
            font.size = None
            font.scale = yex.value.Number.from_tokens(tokens)
            logger.debug(r"  -- scale is: %s",
                    font.scale)
        else:
            font.size = None
            font.scale = None
            logger.debug(r"  -- neither size nor scale are specified")

        return font

    def __getstate__(self,
            name = None):

        if name is None:
            name = self.name

        result = {
                'font': name,
                }

        if self.size is not None:
            result['size'] = self.size.value

        if self.scale is not None:
            result['scale'] = self.scale

        if self.used:
            result['used'] = 1

        if self._custom_dimens:
            result['metrics'] = self._custom_dimens

        if self.hyphenchar != ord('-'):
            result['hyphenchar'] = self.hyphenchar

        if self.skewchar != -1:
            result['skewchar'] = self.skewchar

        return result

    @classmethod
    def from_serial(cls, state):

        name = state['font']

        if isinstance(name, list):
            if name[0]=='nullfont':
                result = yex.font.Nullfont()
            elif name[0]=='default':
                result = yex.font.Default()
            else:
                raise KeyError(name)
        else:
            result = get_font_from_name(name)

        if 'size' in state:
            result.size = yex.value.Dimen(state['size'], 'sp')
        elif 'scale' in state:
            result.scale = yex.value.Number(state['scale'])

        if state.get('used', 0)!=0:
            result.used.add(0) # should be close enough

        if 'metrics' in state:
            result._custom_dimens = state['metrics']

        if 'hyphenchar' in state:
            result.hyphenchar = state['hyphenchar']

        if 'skewchar' in state:
            result.skewchar = state['skewchar']

        return result


    @classmethod
    def from_name(
            cls,
            name,
            doc = None,
            ):
        """
        Given a name, finds a font with that name.

        We return an object of the relevant subclass of yex.font.Font.

        XXX If you request a .pk you get a Glyphs object, not a Font.
        This should be fixed.

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
                    "Font.from_name: returning default font")
            return Default()

        logger.debug(
                "Font.from_name: looking up %s",
                name)

        def _search(name):
            logger.debug(
                    "  -- checking cwd: %s",
                    name)

            if os.path.exists(name):
                logger.debug("    -- found in cwd")

                return (name, open(name, 'rb'))

            logger.debug(
                    "  -- checking resources",
                    )

            in_res = [x for x in
                    (importlib.resources.files(yex) / "res" / "fonts"
                            ).iterdir()
                    if x.name==name
                    ]
            if in_res:
                logger.debug("    -- found in resources")
                return (in_res[0].name, in_res[0].open('rb'))

            name_in_font_dir = os.path.join(
                    os.path.expanduser('~/.fonts'), name)
            logger.debug(
                    "  -- checking user's font dir: %s",
                    name_in_font_dir,
                    )

            if os.path.exists(name_in_font_dir):
                logger.debug("    -- found in user's font dir")
                return (name_in_font_dir, open(name_in_font_dir, 'rb'))

            # FIXME and then try appdirs

            logger.debug(" -- not found")
            return None

        if '.' not in name:
            # for now
            found = _search(name+'.tfm')
        else:
            found = _search(name)

        if found:
            filename, f = found
            name = os.path.splitext(filename)[0]
            if filename.endswith('.tfm'):
                from yex.font.tfm import Tfm
                return Tfm(
                        f = f,
                        name = name,
                        filename = filename,
                        )
            elif filename.endswith('.pk'):
                from yex.font.pk import Glyphs
                return Glyphs(
                        f = f,
                        )
            else:
                raise ValueError(f"Unknown font format: {filename}")

        raise ValueError(f"Unknown font: {name}")

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
