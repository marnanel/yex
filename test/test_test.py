from . import call_macro

def test_test_call_macro_runs_once():
    assert call_macro(
            setup = (
                r"\def\b{Hello{world}}"
                ),
            call = (
                r"\b"
                ),
            )==r"Hello{world}", "call_macro() runs exactly once"
