import logging
import yex
from test import *

logger = logging.getLogger('yex.general')

def test_kern_getstate():
    g = yex.box.Kern(yex.value.Dimen(123, 'pt'))
    assert g.__getstate__()=={'kern': 123*65536}

def test_kern_explicit(capsys):
    g = yex.box.Kern(yex.value.Dimen(123, 'pt'), explicit=True)
    assert g.__getstate__()=={'kern': 123*65536, 'explicit': True}
    assert g.showbox()==[r'\kern 123.0']

    g = yex.box.Kern(yex.value.Dimen(123, 'pt'), explicit=False)
    assert g.__getstate__()=={'kern': 123*65536}
    assert g.showbox()==[r'\kern123.0']

    g = yex.box.Kern(yex.value.Dimen(123, 'pt'))
    assert g.__getstate__()=={'kern': 123*65536}
    assert g.showbox()==[r'\kern123.0']

    run_code(
            r"""
            \setbox0=\hbox{T\kern-.1667emE}\showbox0
            \setbox0=\hbox{We}\showbox0
            """)
    roe = capsys.readouterr()
    assert [kernline for kernline in roe.out.split('\n')
            if 'kern' in kernline]==[
            r'.\kern -1.66702', # we asked for this one
            r'.\kern-0.83334', # implicit kern between "W" and "e"
            ]
