from test import *

def test_chardef(yex_test_fs):
    string = r"\chardef\banana=98wom\banana at"
    assert run_code(string,
            find = "chars") =="wombat"
    string = r"\chardef\dollar=36wom\dollar at"
    assert run_code(string,
            find = "chars") =="wom$at"
