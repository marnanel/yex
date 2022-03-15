from test import run_code

def test_uppercase():
    assert run_code(
            r"\uppercase{I like capybaras.\par Don't you?} Yes.",
            find='ch',
            )==r"I LIKE CAPYBARAS.\parDON'T YOU? Yes."

def test_lowercase():
    assert run_code(
            r"\lowercase{I like capybaras.\par Don't you?} Yes.",
            find='ch',
            )==r"i like capybaras.\pardon't you? Yes."

def test_char_p43():
    assert run_code(
            r'\char98 u\char98\char98 le',
            find='chars',
            )=='bubble'

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
