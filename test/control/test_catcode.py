import yex
from test import *

def test_catcode():
    # We set the catcode of ";" to 14, which makes it
    # a comment symbol.
    string = r";what\catcode`;=14 ;what"
    assert run_code(string,
            find = "chars") ==";what"

def test_catcode_restored():

    for inner_global, expected in [
            ('', 11),
            (r'\global', 12)
            ]:
        saw = run_code(
                r"\catcode42=11{" + inner_global + r"\catcode42=12}*",
                find = 'saw',
                )

        category = [n for n in saw if n.ch=='*'][0].category

        assert category==expected
