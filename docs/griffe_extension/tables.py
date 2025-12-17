from griffe import Object, Extension, Class, Docstring, Package, AliasResolutionError
import inspect
import importlib

TeX = '<span class="tex">T<i>e</i>Χ</span>'

PLACEHOLDER_LINE = '\n[Generated table]'

class TableMaker:

    changing_class_name: str = None
    superclass_path: str = None
    package_to_search_path: str = None
    header: str = None
    footer: str = None

    def describe(self, cls) -> '[(str, str)]':
        raise NotImplementedError()

    def consider(self,
                 pkg:Package,
                 ):
        changing_class = pkg[self.changing_class_name]
        package_to_search = pkg[self.package_to_search_path]

        docstring = changing_class.docstring.value

        parts = docstring.split(PLACEHOLDER_LINE, 1)

        if len(parts)!=2:
            raise ValueError(
                    f'Placeholder line "{PLACEHOLDER_LINE}" '
                    f'not found:\n{docstring}'
                    )

        table_rows = {}

        for name in package_to_search.members:
            try:
                member = package_to_search.get_member(name)
            except KeyError:
                continue

            try:
                bases = member.mro()
            except (AttributeError, AliasResolutionError):
                continue

            if self.superclass_path not in [
                    b.canonical_path for b in bases]:
                continue

            table_rows |= self.describe(changing_class, member)

        changing_class.docstring.value = (
                parts[0] +
                '\n\n' +
                self.header +
                '\n'.join([
                    tr[1] for tr in sorted(table_rows.items())
                    ]) +
                self.footer +
                '\n\n' +
                parts[1]
                )

    def _docstring_for_table_cell(self, cls):
        try:
            result = cls.docstring.value
            result = result.split('\n\n')[0]
            result = result.replace('\n\n', '<br><br>').replace('\n', ' ')
        except AttributeError:
            result = ''

        return result

class TokenTableMaker(TableMaker):

    changing_class_name = 'yex.parse.Token'
    superclass_path = 'yex.parse.token.Token'
    package_to_search_path = 'yex.parse'

    header = f"""
| Category | Subclass | {TeX}? | Short description |
| - | - | - | - |
""".lstrip()

    footer = r"""
| 14 | Comment | yes | Handled internally; never generated |
| 15 | Invalid | yes | Never generated, by definition |
""".lstrip()

    def describe(self, superclass, subclass):

        name = subclass.name

        try:
            category = subclass.get_member('_category')
        except KeyError:
            return ''

        identifier = superclass.get_member(
                str(subclass.get_member('_category').value.last)).value

        # "identifier" is always a str here, which if eval'd would
        # give us the actual identifier
        if identifier[0]=="'":
            is_tex = 'no'
        else:
            is_tex = 'yes'

        docstring = self._docstring_for_table_cell(subclass)

        return [
                (identifier,
                 (
                     f'| {identifier}'
                     f'| [{name}](yex.parse.{name}.md)'
                     f'| {is_tex}'
                     f'| {docstring} '
                     '|'
                     )
                 )
                ]

class GismoTableMaker(TableMaker):

    changing_class_name = 'yex.box.Box'
    superclass_path = 'yex.box.gismo.Gismo'
    package_to_search_path = 'yex.box'

    header = f"""
| Subclass | Symbol | Description |
| - | - | - |
""".lstrip()

    footer = ''

    def describe(self, cls, subclass):

        name = subclass.name

        docstring = self._docstring_for_table_cell(subclass)

        for attempt in [
                lambda: eval(subclass.get_member('_symbol_doc').value),
                lambda: eval(subclass.get_member('_symbol').value),
                lambda: (
                    "["
                    f"{eval(subclass.get_member('single_symbol').value)}"
                    " <i>plus the symbols for its contents</i>"
                    "]"
                    ),
                lambda: '',
                ]:
            try:
                symbol = attempt()
                break
            except (KeyError, AttributeError):
                continue

        symbol = symbol.replace('\n', '<br>')

        return [
                (
                    name,
                    (
                        f'| [{name}](yex.box.{name}.md) '
                        f'| {symbol} '
                        f'| {docstring} '
                        '|'
                        )
                    )
                ]

class KeywordTableMaker(TableMaker):

    changing_class_name = 'yex.control.Control'
    superclass_path = 'yex.control.control.Control'
    package_to_search_path = 'yex.keyword'

    header = f"""
| Identifier | Class | Description |
| - | - | - |
""".lstrip()
    footer = ''

    def describe(self, cls, subclass):

        name = subclass.name

        docstring = self._docstring_for_table_cell(subclass)

        key = name

        if name.startswith('X__'):
            identifier = f"`doc['{name[2:]}']`"
            key = '~'+key # sort them to the end
        elif name.startswith('a_'):
            identifier = chr(int(name[2:], 16))
            if identifier==' ':
                identifier = '\u2420'
        else:
            identifier = '\\' + name.lower()

        return [(
            key,
            (
                rf'| {identifier}'
                f'| [{name}](yex.keyword.{name}.md)'
                f'| {docstring} '
                '|'
                ))]

##############################

class TableMakingExtension(Extension):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_package(
            self,
            pkg: Package,
            *args,
            **kwargs,
            ):

        for maker in [
                TokenTableMaker(),
                GismoTableMaker(),
                KeywordTableMaker(),
                ]:
            maker.consider(pkg)
