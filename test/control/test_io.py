import pytest
import sys
import yex
from test import *

def test_immediate_write_simple(capsys):
    assert run_code(
            r"\immediate\write16{Hello world.}",
            find='chars',
            )==""
    result = capsys.readouterr().out
    assert result.strip()=="Hello world."

def test_immediate_write_side_effect(capsys):
    doc = yex.document.Document()

    assert doc[r'\count1']==0
    assert run_code(
            r"\immediate\write16{Hello \count1=2 world.}",
            find='chars',
            doc=doc,
            )==""
    assert doc[r'\count1']==0

    result = capsys.readouterr().out
    assert result.strip()==r"Hello \count 1=2 world."

def test_write_not_executed(capsys):

    # Let's check that \write does its special handling
    # even when expand=False. We give an obviously
    # silly series of tokens which shouldn't be executed.
    # This wouldn't be a problem anywhere else, but
    # like all the best people, \write is special and weird.

    assert run_code(r"0\iffalse1\write\def\fi2",
            find='chars',
            )=="02"
    result = capsys.readouterr().out
    assert result.strip()==''


# FIXME The following tests check that "write" doesn't crash; they don't
# check that it actually writes to the log. This needs checking.
# In addition, we shouldn't produce anything on the real logs when
# the tests are running!

def test_write_with_single_char_param():
    assert run_code(
            r'\immediate\write-1A',
            )

def test_write_with_complex_param():
    assert run_code(
            r'\immediate\write-1{ABC}',
            )

def test_write_with_string_control():
    assert run_code(
            setup=(
                r'\dimendef\spong=1'
                r'\spong=1pt'
                ),
            call=(
                r'\immediate\write-1{\string\spong}'
                ),
            find='chars',
            )==""

def test_def_wlog():
    assert run_code(
            # from plain.tex
            r"\def\wlog{\immediate\write\mene}",
            find='chars',
            )==''

def test_openin(fs):

    issue_708_workaround()

    with open('wombat.tex', 'w') as f:
        f.write('I like wombats')

    found = run_code(
            (
                r'\openin1=wombat'
                r'\read1 to \wombat '
                r'Yes, \wombat very much'
                ),
            find='ch',
            )

    assert found=='Yes, I like wombats very much'

def test_global_read(fs):

    issue_708_workaround()

    with open('wombat.tex', 'w') as f:
        f.write('Wombat after\n')
        f.write('Spong after\n')

    doc = yex.Document()

    found = run_code(
            (
                r'\openin1=wombat'
                r'\def\wombat{Wombat before}'
                r'\def\spong{Spong before}'
                r'{'
                r'\global\read1 to \wombat'
                r'\read1 to \spong'
                r'}'
                r'(\wombat)(\spong)'
                ),
            doc=doc,
            find='ch',
            )

    assert doc[r'\wombat'].__getstate__()['definition']=='Wombat after '
    assert doc[r'\spong'].__getstate__()['definition']=='Spong before'

def test_closein(fs, capsys):

    issue_708_workaround()

    class FakeStdin:
        def __init__(self, lines):
            self.lines = iter(lines)

        def readline(self):
            return next(self.lines)

    fake_stdin = FakeStdin([
        'This is terminal input: one',
        'This is terminal input: two',
        'This is terminal input: three',
        'This is terminal input: four',
        ])

    old_stdin = sys.stdin
    sys.stdin = fake_stdin

    with open('wombat.tex', 'w') as f:
        f.write('This is file input: one\n')
        f.write('This is file input: two\n')
        f.write('This is file input: three\n')

    found = run_code(
            (
                r'\read1 to \wombat(\wombat)'
                r'\openin1=wombat'
                r'\read1 to \wombat(\wombat)'
                r'\closein1'
                r'\read1 to \wombat(\wombat)'
                ),
            find='ch',
            )

    assert found==(
        '(This is terminal input: one )'
        '(This is file input: one )'
        '(This is terminal input: two )'
        )

    found = run_code(
            (
                r'\read1 to \wombat(\wombat)'
                r'\openin1=somethingelse'
                r'\read1 to \wombat(\wombat)'
                r'\closein1'
                r'\read1 to \wombat(\wombat)'
                ),
            find='ch',
            )

    assert found==(
        '(This is terminal input: three )'
        '()'
        '(This is terminal input: four )'
        )

    sys.stdin = old_stdin
    dummy = capsys.readouterr()

def test_openout(fs):

    issue_708_workaround()

    run_code(
            (
                r'\immediate\openout1=wombat'
                r'\immediate\write1{Wombat}'
                ),
            find='ch',
            )

    with open('wombat.tex', 'r') as f:
        found = f.read()

    assert found=='Wombat'
