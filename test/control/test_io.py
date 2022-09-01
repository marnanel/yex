import pytest
import yex.document
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

    assert doc['count1'].value==0
    assert run_code(
            r"\immediate\write16{Hello \count1=2 world.}",
            find='chars',
            doc=doc,
            )==""
    assert doc['count1'].value==2

    result = capsys.readouterr().out
    assert result.strip()=="Hello world."

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
                r'\read1 to \wombat'
                r'Yes, \wombat very much'
                ),
            find='ch',
            )

    result = capsys.readouterr().out

    assert result=='Yes, I like wombats very much'

def test_closein(fs):

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
        ])

    old_stdin = sys.stdin
    sys.stdin = fake_stdin

    with open('wombat.tex', 'w') as f:
        f.write('This is file input: one')
        f.write('This is file input: two')
        f.write('This is file input: three')

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

    assert result==(
        'This is terminal input: one\n'
        'This is file input: one\n'
        'This is terminal input: two\n'
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

    assert result==(
        'This is terminal input: one\n'
        'This is terminal input: two\n'
        'This is terminal input: three\n'
        )

    sys.stdin = old_stdin

def test_openout(fs):

    issue_708_workaround()

    run_code(
            (
                r'\immediate\openout1=wombat'
                r'\immediate\write1{Wombat}'
                ),
            find='ch',
            )

    with open('wombat.tex', 'w') as f:
        found = f.read()

    assert found=='Wombat'
