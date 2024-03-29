import os
import yex
import collections

PATH = ''

AUTOGENERATED = f'Autogenerated by {__file__}. Do not edit!'

# symbols for the controls table

ACTIVE_CHARACTER = '🤸'
EXPANDABLE = '🪗'
NOT_VISIBLE = '👻'
NOT_IMPLEMENTED = '👽'
HORIZ_SIGN = '↔️'
VERT_SIGN = '↕️ '
MATH_SIGN = 'Σ'

def write(filename, content):
    if os.path.exists(filename):
        existing = open(filename, 'r').read()

        if existing==content:
            print(f'  -- {filename} is up to date')
            return

    print(f'  -- writing {filename}')
    with open(filename, 'w') as f:
        f.write(content)

def icon_for(group):

    icon_filename = os.path.join('symbols',
            f'icon-{group}.png')

    if not os.path.exists(os.path.join(PATH, icon_filename)):
        return ''

    SIZE = '10em'

    return f"""```{{eval-rst}}
.. image:: {icon_filename}
  :alt: {group}
  :class: bg-primary
  :width: {SIZE}
  :height: {SIZE}
  :align: right
```
"""

def document_group(name, filename, instances,
        is_parameter):

    if name in ['control', 'table']:
        return

    if is_parameter:
        typename = name.title()
        if typename=='Int':
            typename = 'Number'

        docstring_source = yex.control.__dict__.get(
                f'C_{typename}Parameter', None)
    else:
        docstring_source = yex.control.__dict__[name]

    if docstring_source is not None:
        docstring = docstring_source.__doc__
    else:
        docstring = None

    if docstring is None:
        title = name
        details = ''
    else:
        lines = docstring.strip().split('\n')
        title = lines[0]

        if title.endswith('.'):
            title = title[:-1]

        details = '\n'.join(lines[1:]).strip()

    result = ''
    result += f'<!--\n{AUTOGENERATED}\n-->\n\n'

    if is_parameter:
        result += icon_for(f'control-parameter')
    else:
        result += icon_for(f'control-{name}')

    result += '# ' + title + '\n'
    result += '\n'

    result += details + '\n\n'

    for name, cls in sorted(instances.items()):

        admonitions = []

        if name.startswith('C_'):
            continue
        elif name.startswith('X_'):
            control_name = name[2:].lower()

            admonitions.append(
                    "This class should not be accessed from TeX code, "
                    "so it has been given a name beginning with `X_`.\n"
                    "That prefix is stripped when placing it in the\n"
                    "document's dictionary, so you will find this control\n"
                    f"at `doc['{control_name}'].\n"
                    )
        elif name.startswith('S_'):
            if name=='S_0020':
                control_name = '&#x5c;␣'
            else:
                control_name = '&#x5c;' + chr(int(name[2:], 16))

            admonitions.append(
                    "This control has a name which can't be\n"
                    "directly represented in Python, so it's given\n"
                    "as a hex codepoint instead. You can find it\n"
                    "in the document dictionary at:\n\n"
                    "```\n"
                    fr"doc['\{chr(int(name[2:], 16))}']"
                    "\n"
                    "```\n"
                    )
        else:
            control_name = '\\' + name.lower()

        if issubclass(cls, yex.control.C_Expandable):
            admonitions.append(
                    "This is an expandable control."
                    )

        try:
            cls()(None)
        except NotImplementedError:
            admonitions.append('Not yet implemented.\n')
        except Exception:
            pass

        result += f'## {control_name}\n'

        for admonition in admonitions:
            result += '<div class="admonition note">\n'
            result += f'{admonition}\n'
            result += '</div>\n\n'

        result += '```{eval-rst}\n'
        result += f'.. autoclass:: yex.control.{name}\n'
        result += '```\n'
        result += '\n'

    write(filename, result)

def make_control_parameter_docs_list(param_types):
    result = ''
    result += '..\n'
    result += f'  {AUTOGENERATED}\n\n'

    result += '.. toctree::\n'
    result += '  :caption: Parameters\n'
    result += '  :titlesonly:\n'
    result += '\n'

    for name, cls in sorted(param_types.items()):
        result += f'  control-parameter-{name}.md\n'

        filename = f'control-parameter-{name}.md'
        document_group(name,
                os.path.join(PATH, filename), cls,
                is_parameter = True)

    write('control-parameter-docs-list.rst', result)

def make_control_keywords_table():

    result = (
            ".. list-table:: Control keywords\n"
            "  :header-rows: 1\n"
            "  :widths: 1, 1, 1, 5\n"
            "\n"
            "  * - Keyword\n"
            "    - Group\n"
            "    - Notes\n"
            "    - Purpose\n"
            )

    klass = type(object) # type "class". How are you supposed to do this?

    def make_symbol(word):
        # For A_xxxx and S_xxxx names.
        symbol = chr(int(word[2:], 16))

        if symbol==' ':
            symbol = '␣'

        return symbol

    def munge_name(word):
        if word.startswith('X_'):
            return word[2:]
        elif word.startswith('A_'):
            return '``' + make_symbol(word) + '``'
        elif word.startswith('S_'):
            return '``\\' + make_symbol(word) + '``'
        else:
            return '``\\' + word.lower() + '``'

    keywords = dict([
        (munge_name(name), cls) for name, cls in
        yex.control.__dict__.items() if
        isinstance(cls, klass) and
        issubclass(cls, yex.control.C_Control) and
        not name.startswith('C_')])

    for word, cls in sorted(keywords.items()):

        group = cls.__module__.split('.')[-1]

        if group=='parameter':
            if cls.our_type == int:
                group = 'Number'
            else:
                group = cls.our_type.__name__

            group = f"*{group}*"

        notes = ''
        if cls.__name__.startswith('A_'):
            notes += ACTIVE_CHARACTER
        elif cls.__name__.startswith('X_'):
            notes += NOT_VISIBLE

        if issubclass(cls, yex.control.C_Expandable):
            notes += EXPANDABLE

        try:
            cls()(None)
        except NotImplementedError:
            notes += NOT_IMPLEMENTED
        except Exception:
            pass

        if cls.__doc__ is None:
            purpose = '?'
        else:
            first_bit = cls.__doc__.strip().split('\n\n')[0]

            purpose = ' '.join([
                x.strip() for x in first_bit.split('\n')])

        result += (
                f"  * - {word}\n"
                f"    - {group}\n"
                f"    - {notes}\n"
                f"    - {purpose}\n"
                )

    result += '\n'

    write('control-keywords-table.rst', result)

def make_control_docs_list(control_types):
    result = ''
    result += '..\n'
    result += f'  {AUTOGENERATED}\n\n'

    result += '.. toctree::\n'
    result += '  :caption: Controls\n'
    result += '  :titlesonly:\n'
    result += '\n'

    for name, cls in sorted(control_types.items()):
        name = name.split('.')[-1]
        filename = f'control-{name}.md'

        if not filename.startswith('control-parameter-'):
            result += f'  {filename}\n'

        document_group(name,
                os.path.join(PATH, filename), cls,
                is_parameter = False)

    write(
            os.path.join(PATH,
                'control-docs-list.rst'),
            result,
        )

def main():
    print(f'Producing docs for {yex.control}:')

    module = type(yex)

    d = yex.control.__dict__

    control_types = collections.defaultdict(lambda: {})
    parameter_types = collections.defaultdict(lambda: {})

    for f,v in d.items():
        try:
            if f.startswith('C_'):
                continue
            elif issubclass(v, yex.control.C_Parameter):
                if isinstance(v.our_type, tuple):
                    t = v.our_type[0]
                else:
                    t = v.our_type
                parameter_types[t.__name__.lower()][f] = v
            elif (
                    issubclass(v, yex.control.C_Control) and
                    v.__module__.startswith('yex.control.')):
                control_types[
                        v.__module__.split('.')[-1]
                        ][f] = v
            else:
                continue
        except TypeError:
            continue

    make_control_docs_list(control_types)
    make_control_parameter_docs_list(parameter_types)

    make_control_keywords_table()

    print('done.')

if __name__=='__main__':
    main()
