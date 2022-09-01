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
