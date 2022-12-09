import argparse
import warnings
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

def s(x):
    result = str(x)[:-2]
    if not result.startswith('-'):
        result = f' {result}'
    return result

def format_char_table(table, kerns, ligatures):
    result = ('    -- code           w (pt)       h          + d          '
            'ital     notes\n')

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

        # The initial space for v.width is to make the kerns line up
        # neatly with the character widths. Character widths are almost
        # never negative, but kerns usually are.
        dimensions = '%-11s ×%-11s' % (s(v.width), s(v.height))
        if v.depth!=0:
            dimensions += '+%-11s' % (s(v.depth),)
        else:
            dimensions += ' '*12

        if v.tag in ('vanilla', 'kerned'):
            tag = ''
        else:
            tag = v.tag + ' ' + str(v.remainder)

        result += '    --%4s %9s %-30s %-8s %s\n' % (
                    v.codepoint,
                    name_of(chr(v.codepoint)),
                    dimensions,
                    s(v.italic_correction),
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
            result += '      -- kern '
            result += ('\n' + ' '*14).join([
                ' %5s %-8s' % (
                        name_of(k[0])+name_of(k[1]),
                        s(d)[:-2],
                        )
                for k, d in kern_list])
            result += '\n'

    return result

def format_dimens_table(dimens):
    fieldnames = {
            1: 'slant',
            2: 'width of space',
            3: '  -- stretch ditto',
            4: '  -- shrink  ditto',
            5: 'x-height',
            6: 'quad (i.e. em width)',
            7: 'extra space after period',
            }

    # there are others for maths fonts; see p16 of the referenced paper

    result = ''
    for f,v in sorted(dimens.items()):

        if isinstance(v, yex.value.Dimen):
            v = '%11s %10ssp' % (s(v)+'pt', v.value)

        result += '\n'
        result += format_line(
            '%2d: %s' % (f, fieldnames.get(f, '?')),
            value=v)

    return result

def format_line(field,
        value=None,
        metrics=None,
        ):

    if value is None:
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
    elif isinstance(value, (str, int, float, yex.value.Dimen)):
        result += str(value)
    else:
        result += str(type(value)) + ' ' + str(value)

    if field=='param_count':
        result += ', thus:' + format_dimens_table(metrics.dimens)

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

        print(format_line(field, metrics=metrics))

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

def sanity_check_tfm(tfm):
    kerns_in_table = set([x.value for x in tfm.metrics.kern_table])
    kerns_on_pairs = set([x.value for x in tfm.metrics.kerns.values()])

    if kerns_in_table-kerns_on_pairs:
        message = "warning: there are unused entries in the kern table:\n"
        difference = kerns_in_table-kerns_on_pairs
        for i, k in enumerate(tfm.metrics.kern_table):
            message += f'        -- entry {i} == {k} ({k.value}sp)'
            if k.value in difference:
                message += '  <--- here'
            message += '\n'

        message += "    this is probably a bug in yex's font parsing"
        warnings.warn(message)

    if kerns_on_pairs-kerns_in_table:
        warnings.warn(
                "warning: there are kerns in use which "
                "aren't in the font file:\n" +
                str(kerns_on_pairs-kerns_in_table) + " --\n" +
                "this is certainly a bug in yex's font parsing")

##############################

def dump_tfm(filename):

    # it's important that we don't ask Tfm for the glyphs;
    # if we did, it would pull out the .pk file. But we want
    # to look that up ourselves.
    with open(filename, 'rb') as f:
        tfm = yex.font.Tfm(f=f)
        dump_metrics(tfm.metrics)
        sanity_check_tfm(tfm)

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

        ext = os.path.splitext(font_filename.abspath)[1].lower()

        if ext=='.tfm':
            dump_tfm(font_filename)
        elif ext=='.pk':
            dump_pk(font_filename)
        else:
            print("  -- extension unknown")

if __name__=='__main__':
    main()
