import yex
from test import *

def test_control_input_simple(fs):

    with open('wombat.tex', 'w') as wombat:
        wombat.write('Q')

    doc = yex.Document()

    found = run_code(
            call = (
                r'A'
                r'\input wombat '
                r'Z'
                ),
            find = 'ch',
            )

    assert found=='A Q Z'

P379_EXAMPLE_TEX = (
    r'\ifx\macsisloaded\relax\endinput\else\let\macsisloaded=\relax\fi '
    'A'
    )

def test_control_endinput_p379(fs):

    with open('wombat.tex', 'w') as wombat:
        wombat.write(P379_EXAMPLE_TEX)

    doc = yex.Document()

    found = run_code(
            call = (
                r'B'
                r'\input wombat '
                r'C'
                r'\input wombat '
                r'D'
                ),
            find = 'ch',
            )

    assert found=='B A C A D'
