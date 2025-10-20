from test import *
import yex.exception
import pytest

@yex_control_test([r'\let'])
def test_let_p206_1():
    string = r'\let\a=\def \a\b{hello}\b'
    assert run_code(string,
            find = "chars") == 'hello'

@yex_control_test([r'\let'])
def test_let_p206_2():
    string = r'\def\b{x}\def\c{y}'+\
            r'\b\c'+\
            r'\let\a=\b \let\b=\c \let\c=\a'+\
            r'\b\c'
    assert run_code(string,
            find = "chars") == 'xyyx'

@yex_control_test([r'\let'])
def test_let_lhs_is_not_control_or_active():
    string = (
            r'\let5=5'
            )

    with pytest.raises(yex.exception.YexError):
        run_code(string,
                find='chars',
                )

@yex_control_test([r'\let'])
def test_let_rhs_is_not_defined():

    assert run_code(
            setup = (
                r'\def\spong{hello}'
                ),
            output='dummy',
            call = (
                r'1=\wombat;'
                r'\let\wombat=\spong'
                r'2=\wombat;'
                r'\let\wombat=\undefined'
                r'3=\wombat '
                ),
            find='ch',
            )==r'1=\wombat;2=hello;3=\wombat'

    with pytest.raises(yex.exception.YexError):
        assert run_code(
                mode='dummy',
                call = (
                    r'\let\xyzzy=\plugh'
                    )
                )

@yex_control_test([r'\let'])
def test_let_redefined_issue_42():
    string = (
            r"\def\b{B}"
            r"\let\a=\b "
            r"a=\a,b=\b;"
            r"\def\a{A}"
            r"a=\a,b=\b"
            )

    assert run_code(string,
            find='ch')=='a=B,b=B;a=A,b=B'

@yex_control_test([r'\let'])
def test_let_active_character_issue72():
    assert run_code(
            setup=(
                r'\catcode`\A=13\def\b{Hello world}'
                ),
            call=(
                r'\let A\b A'
                ),
            find='ch',
            )=='Hello world'

@yex_control_test([r'\let'])
def test_let_digit_used_in_numerical_constant_p206():
    assert run_code(
            setup=(
                r'\let\zero=0'
                ),
            call=(
                r'100 \count10=100 \the\count10;'
                r'2\zero 0 \count20=2\zero 0 \the\count20 '
                ),
            find='ch',
            )=='100 100;200 00 2'
