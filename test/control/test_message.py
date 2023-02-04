from test import *
import pytest
import yex

def test_message(capsys):
    run_code(r"\message{what}",
            find='chars')
    roe = capsys.readouterr()
    assert roe.out == "what"
    assert roe.err == ""

def test_errmessage(capsys):
    run_code(r"\errmessage{what}",
            find='chars')
    roe = capsys.readouterr()
    assert roe.out == ""
    assert roe.err == "what"

def test_register_array_name_in_params():
    found = run_code(
            setup=r'\count10=177',
            call=(
                r'\def\tenth#1{\the#110}'
                r'\tenth\count'
                ),
            find='ch',
            )
    assert found=='177'

def test_register_table_name_in_params_with_errmessage(capsys):
    # Based on ch@ck in plain.tex.
    # This doesn't parse unless the \message or \errmessage
    # handler is run, but told not to do anything,
    # even when an if statement would ordinarily stop it.
    #
    # This is because the parser ignores all code
    # when it's not executing. That's usually the
    # right answer, but not for \message{} and friends.

    run_code(
            r"\def\check#1{\errmessage{No room for a new #1}}"
            r"\check\dimen",
            find='ch',
            )
    roe = capsys.readouterr()
    assert roe.err == r'No room for a new \dimen'
    assert roe.out == ''

def test_register_table_name_in_params_with_message(capsys):
    # Based on ch@ck in plain.tex.
    # This doesn't parse unless the \message or \errmessage
    # handler is run, but told not to do anything,
    # even when an if statement would ordinarily stop it.
    #
    # This is because the parser ignores all code
    # when it's not executing. That's usually the
    # right answer, but not for \message{} and friends.

    run_code(
            r"\def\check#1{\message{No room for a new #1}}"
            r"\check\dimen",
            find='ch',
            )
    roe = capsys.readouterr()
    assert roe.err == ''
    assert roe.out == r'No room for a new \dimen'
