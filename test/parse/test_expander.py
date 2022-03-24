from test import run_code

def test_newline_during_outer_single():
    # See the commit message for an explanation
    run_code(
        r"\outer\def\a#1{b}"
        r"\a\q %Hello world"
        "\r"
        "\r",
        find = 'ch',
        )
