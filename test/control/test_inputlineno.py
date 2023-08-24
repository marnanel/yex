from test import *

def test_inputlineno():
    string = (
            r"\the\inputlineno"
            '\n'
            r"\the\inputlineno"
            '\n'
            '\n'
            r"\the\inputlineno"
            r"\the\inputlineno"
            )

    assert ''.join([str(x) for x in run_code(string, find='saw')]
            )==r"12[paragraph]44"
