import yex.logging
import appdirs
import os
import glob
import importlib.resources
import yex
from yex.control.control import Control
from typing import Union, Self, BinaryIO, Type

logger = yex.logging.getLogger('font')

APPNAME = 'yex'

class _Charset:
    def __init__(self,
                 font: 'Font',
                 ):
        self.font = font

    def __contains__(self,
                     codepoint: Union[int,str],
                     ) -> bool:
        try:
            self[codepoint]
            return True
        except KeyError:
            return False

    def __getitem__(self,
                     codepoint: Union[int,str],
                     ) -> '_Character':

        if isinstance(codepoint, str):
            codepoint = ord(codepoint)

        return self.font.character_class(
                font = self.font,
                codepoint = codepoint,
                )

class _Metrics:
    r"""
    A collection of metrics about a font. Each subclass of Font defines
    its own subclasses of _Metrics.

    Attributes:
        ligatures (Dict[str, str]): a mapping of two-character strings,
            representing two characters which occur together,
            to strings containing the ligatures which should replace them.

        kerns (Dict[str, Dimen]): a mapping of two-character strings,
            representing two characters which occur together,
            to Dimens representing the change brought about by
            kerning those two characters. Because it represents
            a change, the Dimen may be negative.

        dimens (Dict[int, Dimen]): a mapping of the codes TeX uses
            to represent the dimensions of a font, to the values
            of those dimensions. All the possible int values are
            represented by constants in yex.font.Font.

    Infelicity:
        Just because TeX uses plain ints to refer to the details of
        a font doesn't mean we have to. It's not at all friendly.
    """

    def __init__(self,
                 font: 'Font',
                ):
        raise NotImplementedError()

    def __repr__(self):
        return f'[{self.__class__.__name__} of {self.font}]'

class _Character:
    """
    The details of a particular character in a particular font.

    Attributes:
        font: the Font we belong to
        codepoint: our codepoint in that font
    """
    def __init__(self,
                 font: 'Font',
                 codepoint: int,
                 ):
        self.font = font
        self.codepoint = codepoint
        self.font.used.add(codepoint)

    def _get(self, name):
        raise NotImplementedError()

    @property
    def height(self):
        return self._get('height')

    @property
    def width(self):
        return self._get('width')

    @property
    def depth(self):
        return self._get('depth')

    @property
    def italic_correction(self):
        return self._get('italic')

    @property
    def glyph(self):
        return self.font.glyphs.chars[self.codepoint]

    def __repr__(self):
        if self.codepoint>=32 and self.codepoint<=127:
            character = ' (%s)' % (chr(self.codepoint))
        else:
            character = ''

        return '[%04x%s in %s]' % (
                self.codepoint,
                character,
                self.font,
                )

class Font:
    r"""
    A Font represents a set of glyphs-- that is, the images which go together
    to make written text.

    # Terminology

    Most modern systems use "font" to mean a design of lettering which can
    be scaled to various sizes, and can usually be displayed in various
    styles-- bold, italics, or neither ("roman"). In TeX, this concept is
    called a "typeface", and "font" means a particular typeface at a
    particular size and style.

    TeX's default font is Computer Modern, roman, at 10 points: this has
    the identifier `cmr10`.

    # _Metrics and glyphs

    TeX needs to know two things about any letter in a font:

        * the _metrics_: for example, the width or height of the letter;
        * the _glyph_: what the letter looks like on paper.
          The original TeX uses only bitmap fonts: that is, the glyphs are
          represented by images where every pixel is either black or
          transparent.

    In the original TeX, these live in separate files: `.tfm` files
    contain the metrics, and `.pk` files with otherwise identical names
    contain the glyphs.

    # Overview of the subclasses

    This class is abstract. The factory methods from_serial(), from_tokens(),
    and from_name() will give you instances of the appropriate subclass.

    The subclasses are:

        * yex.font.Nullfont: a font containing no characters
        * yex.font.Default: the metrics of the font Computer Modern,
            roman, 10pt (`"cmr10"`), which is the default font
            in TeX; this is hard-coded so that yex is usable
            even without its resource files
        * yex.font.Tfm: "TeX font metrics" files

    For more information on each, see their documentation.

    Attributes:
        hyphenchar, skewchar: the codepoints in the Document's attributes
            of the same name.
        used (set of int): the indexes of the glyphs we have used so far
            in this run.
        metrics (_Metrics): a table of measurements of each character.
            Subclasses of Font will generally return an instance of
            their own metrics class.
        size (Dimen, or None): the size of the type
        scale (real, or None): how much bigger to make the type
        doc: the Document we belong to
        used: the set of all the codepoints of this font which have
            been looked up since this program started

    I wonder:
        Do we really need to keep hold of hyphenchar and skewchar?
    """

    DIMEN_SLANT_PER_PT = 1
    DIMEN_INTERWORD_SPACE = 2
    DIMEN_INTERWORD_STRETCH = 3
    DIMEN_INTERWORD_SHRINK = 4
    DIMEN_X_HEIGHT = 5
    DIMEN_QUAD_WIDTH = 6
    DIMEN_EXTRA_SPACE = 7

    # σ-params
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

    character_class: Type = _Character
    """
    The class that represents characters in this font.

    Not related to wizards and rogues.
    """

    charset_class: Type = _Charset
    """
    The class that represents the set of all characters
    in this font.
    """

    metrics_class: Type = _Metrics
    """
    The class that represents metrics in this font.
    """

    def __init__(self,
                 f = None,
                 name: Union[str, None] = None,
                 source = None,
                 filename = None,
                 doc: 'yex.document.Document' = None,
                 ):

        if doc is not None:
            self.hyphenchar = doc[r'\defaulthyphenchar']
            self.skewchar = doc[r'\defaultskewchar']
        else:
            self.hyphenchar = ord('-')
            self.skewchar = -1

        self.f = f
        self.used = set()

        if name is not None:
            self.name = name
        elif f is not None:
            self.name = os.path.splitext(os.path.basename(f.name))[0]
        else:
            raise yex.exception.NamelessFontError()

        self.source = source or name
        self.filename = filename

        self._custom_dimens = {}
        self._interword = None

        self.metrics = self.metrics_class(
                font = self,
                )

        self.charset = self.charset_class(
                font = self,
                )

    def __getitem__(self,
                    v: Union[int, str],
                    ) -> Union[_Character, yex.value.Dimen]:
        """
        Looks up details of a character.

        If v is a string of length 1, returns the details of that character.
        If v is an integer, returns font dimension number "v".
        Unknown "v" gets 0pt rather than KeyError.

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

            if v in self.metrics.dimens:
                return self.metrics.dimens[v]

            raise yex.exception.NoSuchFontdimenError(
                    fontname=self.name,
                    allowed=str(list(self.metrics.dimens.keys())),
                    problem=v,
                    )

        elif isinstance(v, str):
            raise TypeError(v)
        else:
            raise TypeError()

    @property
    def interword(self) -> yex.value.Glue:
        if self._interword is None:
            self._interword = yex.value.Glue(
                    space = self[2],
                    stretch = self[3],
                    shrink = self[4],
                    )

        return self._interword

    @property
    def em(self) -> yex.value.Dimen:
        """
        The em-width of this font.
        """
        return self[self.DIMEN_QUAD_WIDTH]

    @property
    def ex(self) -> yex.value.Dimen:
        """
        The x-height of this font.
        """
        return self[self.DIMEN_X_HEIGHT]

    def __setitem__(self,
                    n: int,
                    v: yex.value.Dimen,
                    ):
        if not isinstance(n, int):
            raise TypeError()
        if not isinstance(v, yex.value.Dimen):
            raise TypeError()

        if n not in self.metrics.dimens:
            raise yex.exception.NoSuchFontdimenError(
                    fontname=self.name,
                    allowed=str(list(self.metrics.dimens.keys())),
                    problem=n,
                    )
        elif self.used:
            raise yex.exception.FontdimenIsFixedError()

        logger.debug(
                r"%s: set dimen %s, = %s",
                self, n, v)
        self._custom_dimens[n] = v
        self._interword = None

    def __repr__(self):
        try:
            result = self.identifier
            if self.scale is not None:
                result += f' at {self.scale}pt'
        except AttributeError:
            result = '[unknown font]'

        return result

    @property
    def glyphs(self):
        raise NotImplementedError()

    @property
    def identifier(self) -> str:
        return self.name

    @classmethod
    def from_tokens(
            cls,
            tokens: 'yex.parse.Expander',
            name: str = None,
            doc: Union['yex.document.Document', None] = None,
            ) -> Self:
        """
        Given an Expander positioned just before the specification of a font,
        finds that font.

        We return an object of the relevant subclass of yex.font.Font.

        Args:
            tokens: the Expander
            doc: use this document for getting the default
                skewchar and hyphenchar. If this is None, hyphenchar
                is a hyphen, and there is no skewchar.

        Raises:
            ValueError: if there is no font with the given name, or if
                the named file isn't a font.

            YexError: if the next tokens in the expander don't specify a font,
                including when we're at EOF.
        """

        filename = yex.filename.Filename.from_tokens(
                tokens = tokens,
                default_extension = None,
                )

        logger.debug(r"Font.from_tokens: the filename is: %s",
                filename)

        font = cls.from_name(
                name = name,
                source = filename,
                doc = doc,
                )

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
                     name = None,
                     ) -> dict:
        if name is None:
            name = self.name

        result = {
                'font': name,
                'source': self.source,
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
    def from_serial(cls,
                    state:dict,
                    ) -> Self:

        name = state['font']

        if isinstance(name, list):
            if name[0]=='nullfont':
                result = yex.font.Nullfont()
            elif name[0]=='default':
                result = yex.font.Default()
            else:
                raise KeyError(name)
        else:
            result = cls.from_name(name)

        if 'source' in state:
            result.source = state['source']

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
            name: Union[str, 'yex.Filename', None],
            source: str = None,
            doc: 'yex.document.Document' = None,
            ) -> Self:
        """
        Given a name, finds a font with that name.

        We return an object of the relevant subclass of yex.font.Font.

        Args:
            name: the name of the font.
                For example, `"/usr/fonts/cmr10.tfm"` or `"cmr10"`.
                `None` will get you the default font (`yex.font.Default`)
                whose metrics are hard-coded.
            doc: use this document for getting the default
                skewchar and hyphenchar. If this is None, hyphenchar
                is a hyphen, and there is no skewchar.

        Raises:
            ValueError: if there is no font with the given name, or if
                the named file isn't a font.
        """

        return cls._from_name(
                name = name,
                source = source,
                doc = doc,
                find_pk = False,
                )

    @classmethod
    def _from_name(
            cls,
            name: Union[str, 'yex.Filename', None],
            find_pk: bool,
            source: str = None,
            doc: 'yex.document.Document' = None,
            ) -> Self:

        if source is None:
            source = name

        if source is None:
            from yex.font.default import Default

            logger.debug(
                    "Font.from_name: returning default font")
            return Default(name=name)

        logger.debug(
                "Font.from_name: looking up %s",
                source)

        def _search(n):
            logger.debug(
                    "  -- checking cwd: %s",
                    n)

            if os.path.exists(n):
                logger.debug("    -- found in cwd")

                return (n, open(n, 'rb'))

            logger.debug(
                    "  -- checking resources",
                    )

            in_res = [x for x in
                    (importlib.resources.files(yex) / "res" / "fonts"
                            ).iterdir()
                    if x.name==n
                    ]
            if in_res:
                logger.debug("    -- found in resources")
                return (
                        os.path.basename(in_res[0].name),
                        in_res[0].open('rb'),
                        )

            name_in_font_dir = os.path.join(
                    os.path.expanduser('~/.fonts'), n)
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

        if '.' not in source:
            # for now
            found = _search(source+'.tfm')
        else:
            found = _search(source)

        if found:
            filename, f = found
            source = os.path.splitext(filename)[0]
            if filename.endswith('.tfm'):
                from yex.font.tfm import Tfm
                return Tfm(
                        f = f,
                        name = name,
                        source = source,
                        filename = filename,
                        )
            elif find_pk and filename.endswith('.pk'):
                from yex.font.pk import Glyphs
                return Glyphs(
                        f = f,
                        )
            else:
                raise ValueError(f"Unknown font format: {filename}")

        raise ValueError(f"Unknown font: {source}")
