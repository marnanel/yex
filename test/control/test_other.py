from test import run_code
import yex.document

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

def test_control_symbols():
    s = yex.document.Document()

    # Let's look up three controls which are all horizontal unexpandables:

    for name in [
            # an example of a control word:
            r'\discretionary',

            # two examples of control symbols:
            r'\-',
            r'\ ',
            ]:
        handler = s[name]
        assert handler.horizontal, f"{name} is a valid horizontal control"
