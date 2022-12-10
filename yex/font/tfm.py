import struct
import os
import math
import warnings
from collections import namedtuple
from yex.font.font import Font
import logging
import yex.value
import yex.font.pk

logger = logging.getLogger('yex.general')

class Tfm(Font):
    """
    A font in TeX's own TFM format ("TeX Font Metrics").

    TFM files don't contain the glyphs. If you call `glyphs()` on
    a Tfm object, it looks up the corresponding .pk file, which
    should contain the glyphs you need. See `yex.font.pk` for that.

    The format was devised by Lyle Harold in 1980.

    Descriptions of the format:
        * Fuchs, "TeX Font Metric files", TUGboat vol 2 no 1, February 1981:
            https://tug.org/TUGboat/Articles/tb02-1/tb02fuchstfm.pdf
        * the comments around line 10400 of tex.web
        * src/utils/tfmtodit/tfmtodit.cpp in groff
    """
    def __init__(self,
            f,
            size = None,
            scale = None,
            *args, **kwargs,
            ):

        super().__init__(f, *args, **kwargs)

        self.size = size
        self.scale = scale
        self.metrics = Metrics(f)
        self._glyphs = None

    @property
    def glyphs(self):
        if self._glyphs is None:
            self._glyphs = Font.from_name(
                os.path.splitext(self.source)[0]+'.pk',
                )

        return self._glyphs

class CharacterMetric(namedtuple(
    "CharacterMetric",
    "codepoint width_idx height_idx depth_idx "
    "char_ic_idx tag_code remainder "
    "parent",
    )):

    @property
    def tag(self):
        return [
                "vanilla", "kerned", "chain", "extensible",
                ][self.tag_code]

    @property
    def width(self):
        return self.parent.width_table[self.width_idx]

    @property
    def height(self):
        return self.parent.height_table[self.height_idx]

    @property
    def depth(self):
        return self.parent.depth_table[self.depth_idx]

    @property
    def italic_correction(self):
        return self.parent.italic_correction_table[self.char_ic_idx]

    def __repr__(self):
        return ('%(codepoint)3d '+\
               'w%(width)4.2f '+\
               'h%(height)4.2f '+\
               'd%(depth)4.2f '+\
               'i%(italic)-3d '+\
               '%(tag)s') % {
                       'codepoint': self.codepoint,
                       'width': self.width,
                       'height': self.height,
                       'depth': self.depth,
                       'italic': self.italic_correction,
                       'tag': self.tag,
                       }

class Metrics:
    """
    Font metrics, from .tfm files.

    See https://tug.org/TUGboat/Articles/tb02-1/tb02fuchstfm.pdf
    for details of the format.
    """

    def __init__(self, f):

        def unfix(n, em_size=10.0):
            # Decodes integer representations of lengths.
            # See p14 of the referenced document for details.

            a = n>>24

            b = n>>16 & 0xff
            c = n>> 8 & 0xff
            d = n     & 0xff

            if a not in (0x00, 0xff):
                raise ValueError('%08x' % (n,) + ' must begin with 00 or ff')

            length = (b) + (c*2**-8) + (d*2**-16)

            length *= 2**12

            length *= em_size

            length = math.floor(length)

            if a==0xff:
                length -= (2**20 * em_size)

            result = yex.value.Dimen(length, 'sp')

            return result

        # load the actual header

        headers= f.read(12*2)

        file_length, header_table_length, \
                self.first_char, self.last_char, \
                width_table_length, \
                height_table_length, \
                depth_table_length, \
                italic_correction_table_length, \
                lig_kern_program_length, \
                kern_table_length, \
                extensible_char_table_length, \
                self.param_count = \
                struct.unpack(
                    '>'+'H'*12,
                    headers,
                    )

        charcount = self.last_char-self.first_char+1

        if file_length != \
                (6+header_table_length+\
                charcount+ \
                width_table_length+ \
                height_table_length+ \
                depth_table_length+ \
                italic_correction_table_length+ \
                lig_kern_program_length+ \
                kern_table_length+ \
                extensible_char_table_length+ \
                self.param_count):

                    raise ValueError(f"{f.name} does not appear "
                            "to be a .tfm file.")

        # load the table that TeX calls the header.

        header_table = f.read(header_table_length*4)

        def parse_header_table():
            self.checksum = 0
            self.design_size = 0
            self.character_coding_scheme = ''
            self.font_identifier = ''
            self.seven_bit_safe = False
            self.parc_face_byte = 0
            random_word = 0

            # Now, let's see how far we get.
            self.checksum = struct.unpack('>I', header_table[0:4])[0]
            self.design_size = unfix(
                    struct.unpack('>I', header_table[4:8])[0],
                    em_size = 1.0,
                    )
            self.character_coding_scheme = struct.unpack(
                    '40p', header_table[8:48])[0]
            self.font_identifier = struct.unpack(
                    '20p', header_table[48:68])[0]
            random_word = struct.unpack('>I', header_table[68:72])[0]

            # why on earth is it called "random word"?
            self.seven_bit_safe = (random_word&0x8000)!=0
            self.parc_face_byte = random_word&0xF

        try:
            parse_header_table()
        except struct.error:
            pass # not enough stuff in the header

        finfo = struct.unpack(
                f'>{charcount}I',
                f.read(charcount*4),
                )

        self.char_table = dict([
            (charcode,
            CharacterMetric(
                charcode,
                (value & 0xFF000000) >> 24,
                (value & 0x00F00000) >> 20,
                (value & 0x000F0000) >> 16,
                (value & 0x0000FD00) >> 10,
                (value & 0x00000300) >> 8,
                (value & 0x000000FF),
                parent = self,
                    ))
            for charcode, value in
            enumerate(
                finfo,
                start = self.first_char,
                )
            ])

        def get_table(length):
            return [unfix(n) for n in
                    struct.unpack(
                    f'>{length}I',
                    f.read(length*4)
                    )]

        def parse_lig_kern(b):

            # tex.web implies that 'rem' is b&0x7ff if is_kern, but
            # b&0xff otherwise; since those extra three bits aren't
            # used if not is_kern, I don't think it makes a difference.
            # So, both are 0x7ff here. I could be wrong.

            return {
                    'stop': (b>>24)==0x80,
                    'skip': (b>>24) & 0x7f,
                    'second': chr((b>>16)&0xff),
                    'is_kern': ((b >> 8)&0xff)==0x80,
                    'rem': b & 0x7ff, # "remainder" in the sources
                    'hex': '%08x' % (b,), # for debugging
                    }

        self.width_table = get_table(width_table_length)
        self.height_table = get_table(height_table_length)
        self.depth_table = get_table(depth_table_length)
        self.italic_correction_table = \
                get_table(italic_correction_table_length)

        lk = [parse_lig_kern(n) for n in
                    struct.unpack(
                    f'>{lig_kern_program_length}I',
                    f.read(lig_kern_program_length*4)
                    )]

        self.ligatures = {}
        self.kerns = {}

        self.kern_table = get_table(kern_table_length)

        for c in self.char_table.values():
            if c.tag=='kerned':
                index = c.remainder
                while True:
                    instr = lk[index]
                    pair = chr(c.codepoint) + instr['second']

                    if instr['is_kern']:
                        if pair not in self.kerns:
                            self.kerns[pair] = self.kern_table[instr['rem']]

                        # A kern in the table is a terminal condition if
                        # it matches. So if we see what appears to be a
                        # duplicate entry, then we're reading a section which
                        # overlaps with the instructions for a different
                        # first character, and the kern doesn't apply to us.
                        # (There's plenty of overlap used for ligatures,
                        # as a way to save space. Storage was dear in 1980.)
                    else:
                        if pair in self.ligatures:
                            warnings.warn(
                                'More than one ligature '
                                f'was given for "{pair}"')
                        self.ligatures[pair] = chr(instr['rem'])

                    if instr['stop']:
                        break
                    index += instr['skip'] + 1

        # Dimens are specified on p429 of the TeXbook.

        # We're using a dict rather than an array
        # because the identifiers are effectively keys.
        # People might want to delete them and so on,
        # but it would make no sense, say, to shift them all
        # down by one.
        self.dimens = dict([
                (i+1, unfix(n))
                for i, n
                in enumerate(struct.unpack(
                    f'>{self.param_count}I',
                    f.read(self.param_count*4)))
                ])

    def print_char_table(self):
        for f,v in self.char_table.items():
            if f>31 and f<127:
                char = chr(f)
            else:
                char = ' '

            print('%4d %s %s' % (f, char, v))

    def get_character(self, code):
        return self.char_table.get(code)

if __name__=='__main__':
    m = Metrics(
            filename = 'other/cmr10.tfm'
            )
