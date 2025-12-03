from test import *
import yex

def test_string_activechar():
    run_code(r"""\def\tstring#1{\string #1}\tstring{H}""")
