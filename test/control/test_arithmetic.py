from test import *

def test_advance_count():
    assert run_code(
            r'\count10=100'+\
                    r'\advance\count10 by 5 '+\
                    r'\the\count10',
                    find = "chars") == '105'

def test_advance_dimen():
    assert run_code(
            r'\dimen10=10pt'+\
                    r'\advance\dimen10 by 5pt'+\
                    r'\the\dimen10',
                    find = "chars") == '15.0pt'

def test_multiply():
    assert run_code(
            (r'\count10=100'
                r'\multiply\count10 by 5 '
                r'\the\count10'),
            find = "chars") == '500'

def test_divide():
    assert run_code(
            (r'\count10=100'
                r'\divide\count10 by 5 '
                r'\the\count10'),
            find='chars',
            ) == '20'
