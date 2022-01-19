import struct
from collections import namedtuple

class CharacterMetric(namedtuple(
    "CharacterMetric",
    "codepoint width_idx height_idx depth_idx "
    "char_ic_idx tag_code remainder "
    "parent",
    )):

    # TODO: return width etc by lookup in parent

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

            print(self.design_size)
            print(self.character_coding_scheme)
            print(self.font_identifier)

            print(charcount)
            finfo = struct.unpack(
                    f'>{charcount}I',
                    f.read(charcount*4),
                    )
            print(finfo)

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
                result = float(n)/(2**20)
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

            print(self.width_table)

            # TODO: parse lig/kern program
            self.lig_kern_program = get_table(self.lig_kern_program_length)
            # TODO: parse kern table
            self.kern_table = get_table(self.kern_table_length)

            self.slant, self.space, self.spacestretch, \
                    self.spaceshrink, self.xheight, \
                    self.quad, self.extraspace = \
                    [unfix(n) for n in struct.unpack('>7I', f.read(7*4))]
            # plus maybe more fields for the maths-y fonts

            self.print_char_table()

    def print_char_table(self):
        for f,v in self.char_table.items():
            if f>31 and f<127:
                char = chr(f)
            else:
                char = ' '

            print('%4d %s %s' % (f, char, v))

if __name__=='__main__':
    m = Metrics(
            filename = 'other/cmr10.tfm'
            )
