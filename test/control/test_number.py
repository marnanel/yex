from test import *
import yex

def _run(code, expected):
    found = run_code(
            code,
            find='chars',
            )

    assert found==expected

def test_number_p40_simple():
    _run(r"\number24", "24")

def test_number_p40_leading_zeroes_negative():
    _run(r"\number-0015", "-15")

def test_number_p40_register():
    _run(r"\count5=316\number\count5", "316")

def test_romannumeral_p40_simple():
    _run(r"\romannumeral24", r"xxiv")
