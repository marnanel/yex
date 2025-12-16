from griffe import Object, Extension, Class, Docstring
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
                 cls:Class,
                 ):
        if cls.name!=self.class_to_change:
            return

        docstring = cls.docstring.value
        if self.headers in docstring:
            # we've been called twice for some reason
            return

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

class TokenTableMaker(TableMaker):

    class_to_change = 'Token'

    headers = f"""
| Category | Subclass | {TeX}? | Description |
| - | - | - | - |
""".lstrip()

    final_rows = r"""
| 14 | Comment | yes | Handled internally; never generated |
| 15 | Invalid | yes | Never generated, by definition |
""".lstrip()

    def describe(self, cls, tokentype):

        name = tokentype.name

        try:
            category = tokentype.get_member('_category')
        except KeyError:
            return ''

        identifier = cls.get_member(
                str(tokentype.get_member('_category').value.last)).value

        # "identifier" is always a str here, which if eval'd would
        # give us the actual identifier
        if identifier[0]=="'":
            is_tex = 'no'
        else:
            is_tex = 'yes'

        docstring = tokentype.docstring.value
        docstring = docstring.replace('\n\n', '<br><br>').replace('\n', ' ')

        return (
                f'| {identifier}'
                f'| [{name}](yex.parse.{name}.md)'
                f'| {is_tex}'
                f'| {docstring} '
                '|\n'
                )

##############################

class Token_Types(Extension):

    def on_class(
        self,
        cls: Class,
        **kwargs,
        ) -> None:

        for maker in [
                TokenTableMaker(),
                ]:
            maker.consider(cls)
