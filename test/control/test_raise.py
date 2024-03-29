import io
import pytest
from yex.document import Document
from test import *
import yex.font
import yex.put
import yex.box
import yex.value

def test_raise_etc():
    for thing, boxtype, shifted in [
            ('raise',     'hbox',  -1),
            ('lower',     'hbox',   1),
            ('moveleft',  'vbox',  -1),
            ('moveright', 'vbox',   1),
            ]:

        s = Document()
        string = fr'\setbox23=\{thing}3pt\{boxtype}'+'{}'

        run_code(
                string,
                doc=s,
                find='ch',
                )

        box = s[r'\copy23']

        assert box.shifted_by==yex.value.Dimen(shifted*3, 'pt')
