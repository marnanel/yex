import argparse
import yex.filename
import yex.font
import os
import collections
import textwrap

"""
Simple tool to dump font information.

This is useful to check yex is picking up the correct information from
a font file.
"""

def format_char_table(table, kerns, ligatures):
    result = '    -- code          dimensions (pt) ital    notes\n'

    names = collections.defaultdict(lambda: set())

    def name_of(c):
        return ' '.join(names[ord(c)])

    for c, v in table.items():
        if c>=33 and c<=126:
            names[c].add(chr(c))

    for spin_count in range(5):
        problem = set()
        for f, v in ligatures.items():
            label = []
            for c in f:
                if names[ord(c)]:
                    label.append(name_of(c))
                else:
                    label.append(None)

            if None in label:
                problem.add(f)
            else:
                names[ord(v)].add(''.join(label))

        if not problem:
            break

    if problem:
        result += f'  -- probable loop in ligatures table: {problem}\n'

    for c, v in table.items():

        if v.width==0 and v.height==0:
            continue

        if v.depth==0:
            dimensions = '%.2g×%.2g' % (v.width, v.height)
        else:
            dimensions = '%.2g×(%.2g+%.2g)' % (v.width, v.height, v.depth)

        if v.tag in ('vanilla', 'kerned'):
            tag = ''
        else:
            tag = v.tag + ' ' + str(v.remainder)

        result += '    --%4s %9s %-15s %-5.2g %s\n' % (
                    v.codepoint,
                    name_of(chr(v.codepoint)),
                    dimensions,
                    v.italic_correction,
                    tag,
                    )

        if v.codepoint!=c:
            result += (
                    f'      -- codepoint mismatch: c={c}, '
                    f'v has {v.codepoint}'
                    )

        kern_list = [(k, d) for k, d in kerns.items()
            if k.startswith(chr(v.codepoint))
                ]

        if kern_list:
            kern_result = '      -- kerns: '
            kern_result += ', '.join([
                ' %s%s=%-0.gpt' % (
                        name_of(k[0]),
                        name_of(k[1]),
                        d,
                        )
                for k, d in kern_list])

            result += '\n'.join(textwrap.wrap(kern_result))
            result += '\n'

    return result

def format_line(field, metrics):
    value = getattr(metrics, field)

    result = '  -- '+str(field)
    result += '.' * (50-len(result))

    if isinstance(value, bytes):
        result += value.decode('ascii')
    elif isinstance(value, (dict, list)):
        result += '\n'
        if field=='char_table':
            result += format_char_table(value,
                    metrics.kerns, metrics.ligatures)
        else:
            result += str(value)
    elif isinstance(value, (str, int)):
        result += str(value)
    else:
        result += str(type(value))

    return result

def dump_metrics(metrics):
    for field in dir(metrics):

        if field.startswith('_'):
            continue

        if field.endswith('_length'):
            continue

        if field in ('kerns', 'ligatures', 'lig_kern_program',
                'height_table', 'width_table', 'depth_table',
                'italic_correction_table', 'dimens',
                'kern_table', # 'duns_table',
                ):
            continue

        value = getattr(metrics, field)

        if hasattr(value, '__call__'):
            continue

        print(format_line(field, metrics))

    print()

##############################

def dump_glyphs(glyphs):
    for code, ch in sorted(glyphs.chars.items()):
        print('  -- %3d (%s)' % (code, repr(chr(code))))
        print('    --    ', ''.join([str(i)[-1] for i in range(ch.width)]))
        for i, line in enumerate(ch.ascii_art()):
            print('    -- %3d %s' % (i, line))
        print()

##############################

def dump_tfm(filename):

    # it's important that we don't ask Tfm for the glyphs;
    # if we did, it would pull out the .pk file. But we want
    # to look that up ourselves.
    tfm = yex.font.Tfm(filename)
    dump_metrics(tfm.metrics)

def dump_pk(filename):
    with open(filename.path, 'rb') as f:
        pk = yex.font.pk.Glyphs(f)
    dump_glyphs(pk)

def main():
    parser = argparse.ArgumentParser(
            prog = 'yex-show-font',
            description='show information about fonts',
            )

    parser.add_argument('font',
            nargs='+',
            help='source filename')

    args = parser.parse_args()

    for font in args.font:
        font_filename = yex.filename.Filename(font)
        font_filename.resolve()
        print("font:", font_filename,
                '='*(74-len(str(font_filename))))

        ext = os.path.splitext(font_filename.path)[1].lower()

        if ext=='.tfm':
            dump_tfm(font_filename)
        elif ext=='.pk':
            dump_pk(font_filename)
        else:
            print("  -- extension unknown")

if __name__=='__main__':
    main()
