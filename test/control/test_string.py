from test import *

def test_string_simple():
    assert run_code(
            r"\string\def",
            find='chars',
            )==r"\def"

def test_string_with_backslash():
    assert run_code(
            setup=r"\def\thing{a}",
            call=r"\string \thing",
            find='chars',
            )==r"\thing"
