import argparse
import logging
import os
import sys
import yex

logger = logging.getLogger('yex.general')

def run(args):
    doc = yex.Document()

    for filename in args.source:
        with open(filename, 'r') as f:
            doc.read(f)

    import json

    value = doc.__getstate__(full=False)

    args.output.write(
            "############# GENERATED CODE - DO NOT EDIT #############\n")
    args.output.write("""

    import yex

    class Document(yex.Document):
        def __init__(self, *args, **kwargs):
            super().__init__(self, *args, **kwargs))
"""
        )

    for f,v in sorted(value.items()):

        try:
            check = doc[f]
        except KeyError:
            check = None

        if f in ['_full', '_format', '_output']:
            continue
        elif f=='_mode':
            rvalue = f'yex.mode.{v.title()}(self)'
        elif isinstance(v, (int, float, str)):
            rvalue = str(v)
        elif isinstance(check, yex.register.Register):
            rvalue = (
                    f'self.registers["{check.parent.name()}"]'
                    f'[{check.index}]'
                    )
        elif isinstance(check, yex.control.Macro):

            rvalue = (
                    f'yex.control.Macro(\n'
                    f'                {check.definition},\n'
                    f'                {check.parameter_text},\n'
                    f'                {check.starts_at},\n'
                    f'              )'
                    )
            # XXX this is very insufficient!
        else:
            if check is None:
                check_msg = '(NOT in doc)'
            else:
                check_msg = f"cf {check} {type(check)}"

            rvalue = f'{v} {type(v)} -- {check_msg}'

        args.output.write(f'             self["{f}"] = {rvalue}\n')

def main():
    parser = argparse.ArgumentParser(
            prog = __package__,
            description='attempt to turn document state into Python code',
            )

    parser.add_argument('source',
            nargs='+',
            help='source filename')
    parser.add_argument('--output', '-o',
            action='store',
            type=argparse.FileType('w'),
            default=sys.stdout,
            help='output filename (default: stdout)')
    args = parser.parse_args()

    run(args)

if __name__=='__main__':
    main()
