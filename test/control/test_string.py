from test import *

def test_string():
    assert run_code(
            r"\string\def",
            find='chars',
            )==r"\def"
