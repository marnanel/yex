from test import *
import yex.document

@yex_control_test([r'\uppercase'])
def test_uppercase():
    assert run_code(
            r"\uppercase{I like capybaras.\wombat Don't you?} Yes.",
            find='ch',
            )==r"I LIKE CAPYBARAS.\wombatDON'T YOU? Yes."

@yex_control_test([r'\lower', r'\lowercase'])
def test_lowercase():
    assert run_code(
            r"\lowercase{I like capybaras.\wombat Don't you?} Yes.",
            find='ch',
            )==r"i like capybaras.\wombatdon't you? Yes."
