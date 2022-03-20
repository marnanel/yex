import io
import pytest
from yex.state import State
from yex.parse import Tokeniser, Expander
from .. import run_code
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

        s = State()
        string = '\\box23=\\'+thing+'3pt\\'+boxtype+'{}'
        print(string)

        assert run_code(
                string,
                state=s,
                find='ch',
                )==''

        box = s['copy23'].value

        assert box.shifted_by==yex.value.Dimen(shifted*3, 'pt')
