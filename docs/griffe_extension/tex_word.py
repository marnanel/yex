import re
from griffe import Object, Extension, Module, Docstring

REPLACEMENTS = [
    (re.compile(r'\bTeX\b'), '<span class="tex">T<i>e</i>Χ</span>'),
    (re.compile(r'\bTeXbook\b'), '<span class="tex">T<i>e</i>Χbook</span>'),
    ]

class TeX_word(Extension):

    def _change_docstrings(
            self,
            obj:Object,
            ) -> None:
        if obj.docstring:
            for regex, replacement in REPLACEMENTS:
                obj.docstring = Docstring(
                        re.sub(
                            regex,
                            replacement,
                            obj.docstring.value,
                            ))

        for member in obj.members.values():
            if not member.is_alias:
                self._change_docstrings(member)

    def on_module(
        self,
        mod: Module,
        **kwargs,
        ) -> None:

        self._change_docstrings(mod)

Extension = TeX_word
