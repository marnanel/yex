from test import *

def test_inputlineno(yex_test_fs):
    string = (
            r"\the\inputlineno"
            '\n'
            r"\the\inputlineno"
            '\n'
            '\n'
            r"\the\inputlineno"
            r"\the\inputlineno"
            )

    assert run_code(string,
            find='chars',
            )==r"1 2 44"
