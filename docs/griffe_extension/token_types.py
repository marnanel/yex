from griffe import Object, Extension, Class, Docstring
import inspect
import importlib

TeX = '<span class="tex">T<i>e</i>Χ</span>'

TABLE_HEADERS = f"""
| Category | Subclass | {TeX}? | Description |
| - | - | - | - |
""".lstrip()

FINAL_ROWS = """
| 14 | Comment | yes | Handled internally; never generated |
| 15 | Invalid | yes | Never generated, by definition |
""".lstrip()

ATTRIBUTES = "Attributes:"

class Token_Types(Extension):

    def describe(self, cls, tokentype):

        name = tokentype.name
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

    def on_class(
        self,
        cls: Class,
        **kwargs,
        ) -> None:

        if cls.name!='Token':
            return

        docstring = cls.docstring.value
        if TABLE_HEADERS in docstring:
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

            if 'Token' not in [b.name for b in member.bases]:
                continue

            table_rows += self.describe(cls, member)

        docstring = (
                parts[0] +
                TABLE_HEADERS +
                table_rows +
                FINAL_ROWS +
                '\n\n' +
                ATTRIBUTES +
                parts[1]
                )

        cls.docstring.value = docstring

Extension = Token_Types
