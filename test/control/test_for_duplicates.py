import inspect
import yex.control
import collections
import re

MODULE = yex.control

# Doing the search with REs is pretty hacky, but introspection won't work
# because redefinition hides the first instance. Unless I'm wrong.
# I've asked at https://stackoverflow.com/questions/74171893/ ,
# so let's see.

BEFORE_OPEN_BRACKET = re.compile(r'\s*(class|def)\s*([a-zA-Z0-9_]+)\s*\(')

def test_for_duplicates():

    found = collections.defaultdict(lambda: [])

    for module_name in dir(MODULE):
        module = getattr(yex.control, module_name)

        if not inspect.ismodule(module):
            continue

        if module.__package__!=MODULE.__name__:
            continue

        with open(module.__file__, 'r') as f:

            decorator_this_line = False

            for line in f:

                if not line.startswith('  '):
                    decorator_previous_line = decorator_this_line
                    decorator_this_line = \
                            line.startswith('@yex.decorator.control') or \
                            line.startswith('@conditional')

                matched = BEFORE_OPEN_BRACKET.match(line)
                if not matched:
                    continue

                if matched.groups()[0]=='def' and not decorator_previous_line:
                    continue

                found[matched.groups()[1]].append(module_name)

    defined_more_than_once = [(k,v) for k,v in found.items() if len(v)>1]

    assert defined_more_than_once == [], \
            'whether some controls were defined more than once'
