from test import *

@yex_control_test([r'\advance'])
def test_advance_count():
    assert run_code(
            r'\count10=100'+\
                    r'\advance\count10 by 5 '+\
                    r'\the\count10',
                    find = "chars") == '105'

@yex_control_test([r'\advance'])
def test_advance_count_negative():
    assert run_code(
            setup = (
                r'\count10=100 '
                ),
            call=(
                r'\advance\count10 by -5 '
                r'\the\count10'
                ),
            find = "chars") == '95'

    assert run_code(
            setup = (
                r'\count10=100 '
                r'\count11=10'
                ),
            call=(
                r'\advance\count10 by -\count11 '
                r'\the\count10'
                ),
            find = "chars") == '90'

@yex_control_test([r'\advance'])
def test_advance_dimen():
    assert run_code(
            r'\dimen10=10pt'+\
                    r'\advance\dimen10 by 5pt'+\
                    r'\the\dimen10',
                    find = "chars") == '15.0pt'

@yex_control_test([r'\multiply'])
def test_multiply():
    assert run_code(
            (r'\count10=100'
                r'\multiply\count10 by 5 '
                r'\the\count10'),
            find = "chars") == '500'

@yex_control_test([r'\divide'])
def test_divide():
    assert run_code(
            (r'\count10=100'
                r'\divide\count10 by 5 '
                r'\the\count10'),
            find='chars',
            ) == '20'
