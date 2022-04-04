from test import *

def test_catcode(yex_test_fs):
    # We set the catcode of ";" to 14, which makes it
    # a comment symbol.
    string = r";what\catcode`;=14 ;what"
    assert run_code(string,
            find = "chars") ==";what"
