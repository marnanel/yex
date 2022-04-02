from test import *
import pytest

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

@pytest.mark.xfail
def test_special():
    found = {'x': None}
    def handle_string(self, name, s):
        found['x'] = s

    yex.control.Special.handle_string = handle_string
    run_code(r"\special{what}",
            find='chars')

    assert found['x'] == "what"

def test_register_table_name_in_message(capsys):
    # Based on ch@ck in plain.tex.
    # This doesn't parse unless the \errmessage
    # handler is run, but told not to do anything,
    # even when an if statement would ordinarily stop it.
    #
    # This is because the parser run_codes all code
    # when it's not executing. That's usually the
    # right answer, but not for \message{} and friends.

    run_code(
            r"\def\check#1#2{\ifnum\count11<#1"
            r"\else\errmessage{No room for a new #2}\fi}"
            r"\check1\dimen",
            find='chars',
            )
    roe = capsys.readouterr()
    assert roe.err == roe.out == ''
