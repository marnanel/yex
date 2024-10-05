import pytest
import yex
import sys
import tempfile
from test import *

TRACENAMES = [
            'online',
            'macros',
            'stats',
            'paragraphs',
            'pages',
            'output',
            'lostchars',
            'commands',
            'restores',
            ]

def reset_trace():
    """
    especially useful for when capsys has changed sys.stdout,
    so yex.io.trace.streams must be updated
    """
    yex.io.trace.streams = [sys.stdout]

def check_trace(capsys, expect_stdout, expect_file):

    def contents_of_expect_file():
        if expect_file is None:
            return None
        with open(expect_file.name, 'r') as read_back:
            result = read_back.read()
        return result

    yit = yex.io.trace
    assert yit.to_stdout == expect_stdout
    assert yit.target_file == expect_file

    capsys.readouterr() # to flush it
    previous_contents_of_expect_file = contents_of_expect_file()

    yit('thing')

    found_in_stdout = capsys.readouterr().out

    if found_in_stdout=='thing\n':
        assert expect_stdout
    elif found_in_stdout=='':
        assert not expect_stdout
    else:
        raise ValueError(
                f"Unexpected value in stdout: {repr(found_in_stdout)}"
                )

    if expect_file is not None:
        found_in_file = contents_of_expect_file()
        found_in_file = found_in_file[
                len(previous_contents_of_expect_file):]

        if found_in_file=='thing\n':
            assert True
        elif found_in_file=='':
            assert False
        else:
            raise ValueError(
                    f"Unexpected value in log file: {repr(found_in_file)}"
                    )

def test_trace_simple(capsys):

    reset_trace()

    yex.io.trace('octopus')
    assert capsys.readouterr().out == 'octopus\n'

def test_trace_properties(capsys):

    yit = yex.io.trace
    reset_trace()

    with tempfile.NamedTemporaryFile(
            prefix = 'yex.test.',
            suffix = '.log',
            mode = 'w',
            ) as temp:

        check_trace(capsys, expect_stdout=True, expect_file=None)

        yit.to_stdout = False
        check_trace(capsys, expect_stdout=False, expect_file=None)

        yit.target_file = temp
        check_trace(capsys, expect_stdout=False, expect_file=temp)

        yit.to_stdout = True
        check_trace(capsys, expect_stdout=True, expect_file=temp)

        yit.target_file = None
        check_trace(capsys, expect_stdout=True, expect_file=None)

def test_trace_control_names():
    s = yex.Document()

    for name in [fr'\tracing{x}' for x in TRACENAMES]:
        assert s.controls[name] is not None
