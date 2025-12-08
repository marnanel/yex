from test import *
import yex

def test_tokeniser_superscript_symbol_issue_119():
    """
    When a Superscript token is pushed back, then found and pushed back again,
    it neither crashes nor causes infinite recursion.
    This is a regression test.

    If a tokeniser sees a caret in its input,
    """
    run_code(
            r"\def\^{}",
            )
