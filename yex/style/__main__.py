import argparse
import os
import sys
import json
import yex
import logging
import string

logger = logging.getLogger('yex.general')

def bootstrap_catcodes():
    result = [(ord(f), v) for f,v in {
        "\\":  0, # Escape character
        '{':   1, # Beginning of group
        '}':   2, # End of group
        '$':   3, # Math shift
        '&':   4, # Alignment tab
        '\n':  5, # End of line
        '\r':  5,
        '#':   6, # Parameter
        '^':   7, # Superscript
        '_':   8, # Subscript
        '\0':  9, # Ignored character
        ' ':  10, # Space
        # 11: Letter
        # 12: Other
        '~':  13, # Active character
        '%':  14, # Comment character
        chr(127): 15, # Invalid character,
        }.items()]

    for c in string.ascii_letters:
        result.append((ord(c), 11)) # Letter

    return result

class Tabulate():

    def __init__(self,
            name=None,
            indent=0,
            width=78,
            tabstop=8,
            ):
        self.current = None
        self.name = name
        self.indent = indent
        self.width = width
        self.tabstop = tabstop
        self.flush()

    def __enter__(self):
        if self.name is not None:
            print(' ' * (self.indent) + self.name + ' = {')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.flush()
        print(self.current+'}')

    def flush(self, indent=None):
        if self.current:
            print(self.current)
        if indent is None:
            indent = self.indent
        self.current = ' ' * (indent+4)

    def write(self, s, *args, **kwargs):
        msg = s % args
        if kwargs.get('flush', False) or len(self.current)+len(msg)>self.width:
            self.flush(indent=kwargs.get('indent', None))

        self.current += msg
        self.current += ' ' * (self.tabstop-len(self.current)%self.tabstop)

def run(args):

    state = json.load(args.json)
    style_name = os.path.splitext(
            os.path.basename(args.json.name))[0].title()

    print(
            "############# GENERATED CODE - DO NOT EDIT #############")

    print()
    print("from yex.style.style import Style")
    print(f"class {style_name}(Style):")

    # start out including the ones we should ignore
    seen = {
            '_created',
            '_version',
            '_full',
            '_format',
            }

    with Tabulate(name='CATCODES', indent=4) as t:
        if args.bootstrap_catcodes:
            items = bootstrap_catcodes()
        else:
            items = [int(f[8:],v) for f,v in state.items()
                    if f.startswith(r'\catcode')]

        seen.update(dict(items))

        for f,v in sorted(items):
            t.write('%3s: %2s,', f, v)

    print()

    location_filenames = []

    with Tabulate(name='MACROS', indent=4) as t:
        for f,v in state.items():
            if not isinstance(v, dict):
                continue
            if 'macro' not in v:
                continue

            if len(f)==1 and f==v['macro']:
                del v['macro']
            elif len(f)>1 and f[0]=='\\' and f[1:]==v['macro']:
                del v['macro']

            if 'starts_at' in v:
                filename, line, column = v['starts_at'].split(':')
                if filename not in location_filenames:
                    location_filenames.append(filename)

                v['loc'] = (
                        location_filenames.index(filename),
                        int(line),
                        int(column),
                        )

                del v['starts_at']

            seen.add(f)

            t.write('%s: %s,', repr(f), repr(v))

    print()

    with Tabulate(name='LOCATION_FILENAMES', indent=4) as t:
        for f,v in enumerate(location_filenames):
            t.write('%s: %s,', f, repr(v))
    print()

    with Tabulate(name='OTHER', indent=4) as t:
        for f,v in sorted(state.items()):
            if f not in seen:
                t.write('%s: %s,', repr(f), repr(v))

    print()
    print("# eof")

def main():
    parser = argparse.ArgumentParser(
            prog = __package__,
            description='attempt to turn document state into Python code',
            )

    parser.add_argument('json',
            type=argparse.FileType('r'),
            help='JSON state (from "yex --dump")')
    parser.add_argument('--bootstrap-catcodes',
            action='store_true',
            help=(
                "use the standard catcodes; don't attempt to get them"
                "from the JSON"
                ))
    args = parser.parse_args()

    run(args)

if __name__=='__main__':
    main()
