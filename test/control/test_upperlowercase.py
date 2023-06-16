from test import *
import yex.document

def test_uppercase():
    assert run_code(
            r"\uppercase{I like capybaras.\wombat Don't you?} Yes.",
            find='ch',
            )==r"I LIKE CAPYBARAS.\wombatDON'T YOU? Yes."

def test_lowercase():
    assert run_code(
            r"\lowercase{I like capybaras.\wombat Don't you?} Yes.",
            find='ch',
            )==r"i like capybaras.\wombatdon't you? Yes."
