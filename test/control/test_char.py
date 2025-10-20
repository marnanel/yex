from test import *

@yex_control_test([r'\char'])
def test_char_p43():
    assert run_code(
            r'\char98 u\char98\char98 le',
            find='chars',
            )=='bubble'

@yex_control_test([r'\char'])
def test_char_p44():
    assert run_code(
            r'\char98',
            find='chars',
            )=='b', r"decimal \char"

    assert run_code(
            r"\char'142",
            find='chars',
            )=='b', r"octal \char"

    assert run_code(
            r'\char"62',
            find='chars',
            )=='b', r"hex \char"
