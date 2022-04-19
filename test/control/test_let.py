from test import *
import yex.exception
import pytest

def test_let_p206_1():
    string = r'\let\a=\def \a\b{hello}\b'
    assert run_code(string,
            find = "chars") == 'hello'

def test_let_p206_2():
    string = r'\def\b{x}\def\c{y}'+\
            r'\b\c'+\
            r'\let\a=\b \let\b=\c \let\c=\a'+\
            r'\b\c'
    assert run_code(string,
            find = "chars") == 'xyyx'

def test_let_lhs_is_not_control():
    string = (
            r'\let5=5'
            )

    with pytest.raises(yex.exception.YexError):
        run_code(string,
                find='chars',
                )

def test_let_rhs_is_not_defined():

    assert run_code(
            setup = (
                r'\def\spong{hello}'
                ),
            mode='dummy',
            call = (
                r'1=\wombat;'
                r'\let\wombat=\spong'
                r'2=\wombat;'
                r'\let\wombat=\undefined'
                r'3=\wombat '
                ),
                find='tokens',
                )==r'1=\wombat;2=hello;3=\wombat'

    with pytest.raises(yex.exception.YexError):
        assert run_code(
                mode='dummy',
                call = (
                    r'\let\xyzzy=\plugh'
                    )
                )

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
