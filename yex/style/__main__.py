import argparse
import os
import sys
import json
import yex
import logging
import textwrap
import string
import os
import re
import collections

logger = logging.getLogger('yex.general')

OUTPUT_WIDTH = 60

REGISTER = re.compile(r'^\\([a-z]+)([0-9]+)$')

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
            parent=None,
            indent=None,
            width=78,
            ):
        self.current = ''
        self.name = name
        self.parent = parent
        self.width = width

        if indent:
            self.indent = indent
        else:
            self.indent = 4

        self.flush()

    def __enter__(self):
        if self.name is not None:
            message = ' ' * (self.indent)
            if self.parent:
                message += repr(self.name) + ': {'
            else:
                message += self.name + ' = {'

            self.output(message)

        self.indent += 4
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.flush()
        self.indent -= 4
        if self.parent:
            comma = ','
        else:
            comma = ''
        line = (' ' * self.indent) + self.current + '}' + comma
        self.output(line)

        if self.parent:
            self.parent.flush()

    def output(self, line):
        if self.parent:
            self.parent.output(' '*4 + line)
        else:
            print(line)

    def flush(self, indent=None, para=False):

        indent = indent or self.indent
        width = OUTPUT_WIDTH - indent
        indent *= ' '
        subsequent = indent

        if para:
            subsequent += ' ' * 4

        for line in textwrap.wrap(
                self.current,
                width = width,
                initial_indent = indent,
                subsequent_indent = subsequent,
                ):
            self.output(line.rstrip())

        self.current = ''

    def write(self, s, *args, **kwargs):
        msg = s % args
        if kwargs.get('flush', False):
            self.flush(
                    indent=kwargs.get('indent', None),
                    para=kwargs.get('para', False),
                    )

        if kwargs.get('newline', False):
            self.current += msg + '\n'
        else:
            self.current += msg + ', '

def run(args):

    state = json.load(args.json)
    style_name = os.path.splitext(
            os.path.basename(args.json.name))[0].title()

    print("############# GENERATED CODE - DO NOT EDIT #############")
    print("# See yex/style/style.py to learn how to regenerate it #")

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

    registers = collections.defaultdict(
            lambda: {},
            )

    with Tabulate(name='CONTROLS') as t:
        for f,v in state.items():
            if f in seen:
                continue

            match = REGISTER.match(f)
            if match:
                array, index = match.groups()
                registers[array][index] = v
                continue

            if isinstance(v, dict):
                if 'starts_at' in v:
                    filename, line, column = v['starts_at'].split(':')

                    v['loc'] = (
                            os.path.basename(filename),
                            int(line),
                            int(column),
                            )

                    del v['starts_at']

            seen.add(f)

            t.write('%s: %s', repr(f), repr(v),
                    flush=True, para=True,
                    )

    print()

    with Tabulate(name='ARRAYS') as t1:
        for name, values in sorted(registers.items()):
            with Tabulate(name=name, parent=t1) as t2:
                for f,v in values.items():
                    t2.write('%s:%s', f,v)

                    if isinstance(v, dict):
                        t2.flush(para=True)

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
