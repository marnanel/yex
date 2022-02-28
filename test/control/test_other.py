from test import _test_expand

def test_uppercase():
    assert _test_expand(
            r"\uppercase{I like capybaras.\par Don't you?} Yes."
            )==r"I LIKE CAPYBARAS.\parDON'T YOU? Yes."

def test_lowercase():
    assert _test_expand(
            r"\lowercase{I like capybaras.\par Don't you?} Yes."
            )==r"i like capybaras.\pardon't you? Yes."
