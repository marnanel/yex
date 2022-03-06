import io
import pytest
from mex.state import State
from mex.parse import Tokeniser, Expander
from .. import expand, call_macro
import mex.font
import mex.put
import mex.box
import mex.value

def test_raise_etc():
    for thing, boxtype, shifted in [
            ('raise',     'hbox',  -1),
            ('lower',     'hbox',   1),
            ('moveleft',  'vbox',  -1),
            ('moveright', 'vbox',   1),
            ]:

        s = State()
        string = '\\box23=\\'+thing+'3pt\\'+boxtype+'{}'
        print(string)

        assert expand(string, s)==''

        box = s['copy23'].value

        assert box.shifted_by==mex.value.Dimen(shifted*3, 'pt')
