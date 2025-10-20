import re
from griffe import Object, Extension, Module, Docstring

TEX_WORD_RE = re.compile(r'TeX')
TEX_HTML = 'T<i class="tex">e</i>Χ'

class TeX_word(Extension):

    def _change_docstrings(
            self,
            obj:Object,
            ) -> None:
        if obj.docstring:
            if 'TeX' in obj.docstring.value:
                obj.docstring = Docstring(
                        re.sub(
                            TEX_WORD_RE,
                            TEX_HTML,
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
