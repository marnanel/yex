import re
from griffe import Object, Extension, Module, Docstring
import inspect

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
            value = obj.docstring.value
            for regex, replacement in REPLACEMENTS:
                value = re.sub(
                    regex,
                    replacement,
                    value,
                    )
            value = inspect.cleandoc(value)

            obj.docstring.value = value

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
