import struct
import os
from collections import namedtuple
from yex.font.font import Font
import logging
import yex.value
import yex.font.pk

commands_logger = logging.getLogger('yex.commands')

class Tfm(Font):
    def __init__(self,
            filename,
            scale = None,
            *args, **kwargs,
            ):

        super().__init__(*args, **kwargs)

        self.filename = filename
        self.scale = scale
        self.name = filename.basename
        self.metrics = Metrics(self.filename.path)
        self._glyphs = None

    @property
    def glyphs(self):
        if self._glyphs is None:

            pk_filename = yex.filename.Filename(
                name = os.path.splitext(self.filename.value)[0]+'.pk',
                filetype = 'pk',
                )
            pk_filename.resolve()
            commands_logger.debug("loading font glyphs from %s",
                pk_filename)
            with open(pk_filename.value, 'rb') as f:
                self._glyphs = yex.font.pk.Glyphs(f)

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

    def __repr__(self):
        return ('%(codepoint)3d '+\
               'w%(width)4.2f '+\
               'h%(height)4.2f '+\
               'd%(depth)4.2f '+\
               'c%(char_ic_idx)-3d '+\
               '%(tag)s') % {
                       'codepoint': self.codepoint,
                       'width': self.width,
                       'height': self.height,
                       'depth': self.depth,
                       'char_ic_idx': self.char_ic_idx,
                       'tag': self.tag,
                       }

class Metrics:

    # Font metrics, from TFM files. See
    # https://tug.org/TUGboat/Articles/tb02-1/tb02fuchstfm.pdf
    # for details of the format.

    def __init__(self, filename):
        with open(filename, 'rb') as f:

            # load the actual header

            headers= f.read(12*2)

            self.file_length, self.header_table_length, \
                    self.first_char, self.last_char, \
                    self.width_table_length, \
                    self.height_table_length, \
                    self.depth_table_length, \
                    self.italic_correction_table_length, \
                    self.lig_kern_program_length, \
                    self.kern_table_length, \
                    self.extensible_char_table_length, \
                    self.param_count = \
                    struct.unpack(
                        '>'+'H'*12,
                        headers,
                        )

            charcount = self.last_char-self.first_char+1

            if self.file_length != \
                    (6+self.header_table_length+\
                    charcount+ \
                    self.width_table_length+ \
                    self.height_table_length+ \
                    self.depth_table_length+ \
                    self.italic_correction_table_length+ \
                    self.lig_kern_program_length+ \
                    self.kern_table_length+ \
                    self.extensible_char_table_length+ \
                    self.param_count):

                        raise ValueError(f"{filename} does not appear "
                                "to be a .tfm file.")

            # load the table that TeX calls the header.
            # For some reason it's always 18*4 bytes long,
            # not necessarily the length of header_table_length.

            header_table = f.read(18*4)

            self.checksum, \
                    self.design_size, \
                    self.character_coding_scheme, \
                    self.font_identifier, \
                    self.random_word = \
                    struct.unpack(
                            '>II40p20pI',
                            header_table,
                            )

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
                    (value & 0x0000000F),
                    parent = self,
                        ))
                for charcode, value in
                enumerate(
                    finfo,
                    start = self.first_char,
                    )
                ])

            def unfix(n):
                # Turns a signed 4-byte integer into a real number.
                # See p14 of the referenced document for details.
                result = (float(n)/(2**20))*10
                return result

            def get_table(length):
                return [unfix(n) for n in
                        struct.unpack(
                        f'>{length}I',
                        f.read(length*4)
                        )]
            self.width_table = get_table(self.width_table_length)
            self.height_table = get_table(self.height_table_length)
            self.depth_table = get_table(self.depth_table_length)
            self.italic_correction_table = \
                    get_table(self.italic_correction_table_length)

            # TODO: parse lig/kern program
            self.lig_kern_program = get_table(self.lig_kern_program_length)
            # TODO: parse kern table
            self.kern_table = get_table(self.kern_table_length)

            # Dimens are specified on p429 of the TeXbook.
            # We're using a dict rather than an array
            # because the identifiers are effectively keys.
            # People might want to delete them and so on,
            # but it would make no sense, say, to shift them all
            # down by one.
            self.dimens = dict([
                    (i+1, yex.value.Dimen(unfix(n), 'pt'))
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
