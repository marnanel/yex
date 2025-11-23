from test import *
import pytest
import yex

class BoxExpecter:
    def __init__(self, expected):
        self.i = 0
        self.expected = expected

    def __call__(self, expander, item):
        self.i += 1

        if isinstance(item, yex.box.Box):
            return ' '.join(
                    [
                        word.ch for word in item
                        if isinstance(word, yex.box.WordBox)])
        else:
            return str(item)

@yex_control_test([r'\box', r'\hbox', r'\lastbox', r'\setbox'])
def test_lastbox():
    on_each = BoxExpecter(
            expected=[],
            )

    found = run_code(
            call=(
                r"Tuesday \hbox{we are}\setbox17=\lastbox meeting Yoda \box17"
                ),
            on_each=on_each,
            find='items',
            )

    assert ''.join([
        n.ch for n in found
        ]).strip()=='Tuesday meeting Yoda we are'
