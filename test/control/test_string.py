from test import *

def test_string(yex_test_fs):
    assert run_code(
            r"\string\def",
            find='chars',
            )==r"\def"
