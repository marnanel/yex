from test import *

def test_penalty():
    saw = run_code(
            r"a\penalty 50b\penalty-500c",
            find='saw',
            strip = True,
            )

    assert [str(x) for x in saw] == [
            'a',
            '[penalty: 50]',
            'b',
            '[penalty: -500]',
            'c',
            ]
