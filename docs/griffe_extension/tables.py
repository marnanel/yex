from griffe import Object, Extension, Class, Docstring, Package
import inspect
import importlib

TeX = '<span class="tex">T<i>e</i>Χ</span>'

ATTRIBUTES = "Attributes:"

class TableMaker:

    class_to_change: str = None
    headers: str = None
    final_rows: str = None

    def describe(self, cls) -> str:
        raise NotImplementedError()

    def consider(self,
                 pkg:Package,
                 ):
        cls = pkg[self.class_to_change]

        docstring = cls.docstring.value

        parts = docstring.split(ATTRIBUTES, 1)

        if len(parts)!=2:
            raise ValueError(f"Attributes header not found:\n{docstring}")

        table_rows = ''

        for name in cls.module.members:
            member = cls.module.get_member(name)
            if not isinstance(member, Class):
                continue

            if self.class_to_change not in [
                    b.name for b in member.bases]:
                continue

            table_rows += self.describe(cls, member)

        cls.docstring.value = (
                parts[0] +
                self.headers +
                table_rows +
                self.final_rows +
                '\n\n' +
                ATTRIBUTES +
                parts[1]
                )

    def _docstring_for_table_cell(self, cls):
        try:
            result = cls.docstring.value
            result = result.replace('\n\n', '<br><br>').replace('\n', ' ')
        except AttributeError:
            result = ''

        return result

class TokenTableMaker(TableMaker):

    class_to_change = 'yex.parse.Token'

    headers = f"""
| Category | Subclass | {TeX}? | Description |
| - | - | - | - |
""".lstrip()

    final_rows = r"""
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

        return (
                f'| {identifier}'
                f'| [{name}](yex.parse.{name}.md)'
                f'| {is_tex}'
                f'| {docstring} '
                '|\n'
                )

class GismoTableMaker(TableMaker):

    class_to_change = 'yex.box.Gismo'

    headers = f"""
| Subclass | Symbol | Description |
| - | - | - |
""".lstrip()

    final_rows = ''

    def describe(self, cls, subclass):

        name = subclass.name

        docstring = self._docstring_for_table_cell(subclass)

        try:
            symbol = subclass.get_member('_symbol_doc').value
        except (KeyError, AttributeError):
            try:
                symbol = subclass.get_member('_symbol').value
            except (KeyError, AttributeError):
                symbol = '-'

        return (
                f'| [{name}](yex.gismo.{name}.md)'
                f'| {symbol}'
                f'| {docstring} '
                '|\n'
                )

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
                ]:
            maker.consider(pkg)
