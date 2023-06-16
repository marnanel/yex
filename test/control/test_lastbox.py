from test import *
import pytest
import yex

class BoxExpecter:
    def __init__(self, expected):
        self.i = 0
        self.expected = expected

    def __call__(self, expander, item):
        self.i += 1

def test_lastbox():
    on_each = BoxExpecter(
            expected=[],
            )

    found = run_code(
            call=(
                r"Tuesday \hbox{we are}\setbox17=\lastbox meeting Yoda \box17"
                ),
            on_each=on_each,
            find='ch_list',
            )

    assert found=='Tuesday meeting Yoda we are'
