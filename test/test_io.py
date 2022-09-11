import pytest
import string
import sys
import yex
from test import *

WOMBAT_TEX = 'wombat.tex'

TEST_DATA = r"""This contains } some number { of
matching } lines
But\par if there is { some set} of } braces
Then it will { read
onto the } next line as well"""

class FakeStdin:
    def __init__(self, lines):
        self.lines = iter(lines)

    def readline(self):
        return next(self.lines)

def _expected_parse(doc):
    return [
            (False, ['This contains']),
            (False, ['matching']),
            (False, ['But',
                yex.parse.Control(r'par', doc=doc, location=None),
                'if there is ',
                yex.parse.BeginningGroup(ch='{'),
                ' some set',
                yex.parse.EndGroup(ch='}'),
                ' of']),
            (False, ['Then it will ',
                yex.parse.BeginningGroup(ch='{'),
                ' read onto the ',
                yex.parse.EndGroup(ch='}'),
                ' next line as well']),
            (True, [yex.parse.Control(r'par', doc=doc, location=None)]),
            (True, None),
            ]

def test_io_streams_exist():
    doc = yex.document.Document()
    assert doc['_inputs;-1'] is not None
    assert doc['_inputs;0'] is not None
    assert doc['_inputs;1'] is not None
    assert doc['_inputs;15'] is not None
    assert doc['_inputs;16'] is not None

    assert doc['_outputs;-1'] is not None
    assert doc['_outputs;0'] is not None
    assert doc['_outputs;1'] is not None
    assert doc['_outputs;15'] is not None
    assert doc['_outputs;16'] is not None

def test_io_write_to_terminal(capsys):

    doc = yex.document.Document()
    string = 'Hello world\rHurrah'

    terminal = yex.io.OutputStream.on_terminal(doc=doc, number=0)
    terminal.write(string)
    result = capsys.readouterr().out

    assert result==string.replace('\r', '\n')

def test_io_write_to_file(fs, capsys):

    issue_708_workaround()

    def contents():
        with open('fred.tex', 'r') as f:
            return f.read()

    doc = yex.Document()

    output_stream = doc[r'_outputs;1'].open(
            filename = 'fred',
            )

    assert contents()==''

    output_stream.write('Hello world\n')
    assert contents()=='Hello world\n'

    output_stream.write('I like cheese\n')
    assert contents()=='Hello world\nI like cheese\n'

    output_stream.close()
    assert contents()=='Hello world\nI like cheese\n'

    with pytest.raises(ValueError):
        output_stream.write('Writing after close')

    doc['_outputs;1'].write('But there is still cheese\n')
    assert contents()=='Hello world\nI like cheese\n'

    result = capsys.readouterr().out
    assert result=='But there is still cheese\n'

def test_io_read_from_terminal():

    fake_stdin = FakeStdin(TEST_DATA.split('\n'))

    old_stdin = sys.stdin
    sys.stdin = fake_stdin

    doc = yex.Document()

    tis = yex.io.InputStream.on_terminal(
            doc=doc,
            number = 1,
            )

    for expect_eof, line in _expected_parse(doc):
        expected = _munge_tokens(line,
                add_space = not expect_eof)

        found = tis.read()

        assert expected==found, line
        assert tis.eof == expect_eof

    tis.close() # no-op

    sys.stdin = old_stdin

def _munge_tokens(t, add_space=True):

    if t is None:
        return None

    result = []
    for thing in t:
        if isinstance(thing, str):
            for ch in thing:
                if ch in string.ascii_lowercase+string.ascii_uppercase:
                    category = yex.parse.Token.LETTER
                else:
                    category = None

                result.append(yex.parse.get_token(
                    ch=ch,
                    category=category,
                    ))
        else:
            result.append(thing)

    if add_space:
        result.append(yex.parse.Space(ch=' '))

    return result

def test_io_read_from_file(fs):

    issue_708_workaround()
    doc = yex.Document()

    with open('fred.tex', 'w') as fred:
        fred.write(TEST_DATA)

    input_stream = yex.io.InputStream(
            doc = doc,
            number = 1,
            filename = 'fred.tex',
            )
    assert not input_stream.eof

    for expect_eof, line in _expected_parse(doc):
        expected = _munge_tokens(line,
                add_space = not expect_eof)

        found = input_stream.read()

        assert expected==found, line
        assert input_stream.eof == expect_eof

    input_stream.close()
    assert input_stream.eof

def test_io_read_from_closed_file(fs):

    issue_708_workaround()
    doc = yex.Document()

    with open('fred.tex', 'w') as fred:
        fred.write(TEST_DATA)

    input_stream = doc[r'_inputs;1'].open(
            filename = 'fred.tex',
            )

    assert not input_stream.eof

    found = input_stream.read()
    assert found==_munge_tokens(['This contains'])
    assert not input_stream.eof

    input_stream.close()
    assert input_stream.eof

    found = input_stream.read()
    assert found is None

def test_io_read_from_file_not_found(fs):
    doc = yex.Document()

    input_stream = yex.io.InputStream(
            doc = doc,
            number = 1,
            filename = 'gronda.tex',
            )

    assert input_stream.eof
    found = input_stream.read()
    assert found is None

def test_io_read_supplies_file_extension(fs):

    issue_708_workaround()
    doc = yex.Document()

    with open(WOMBAT_TEX, 'w') as f:
        f.write('wombat')
    with open('spong.html', 'w') as f:
        f.write('spong')

    for filename, expected in [
            ('wombat', 'wombat'),
            (WOMBAT_TEX, 'wombat'),
            ('wombat.html', None),
            ('spong', None),
            ('spong.html', 'spong'),
            ]:

        input_stream = yex.io.InputStream(
                doc = doc,
                number = 1,
                filename = filename,
                )

        expected = _munge_tokens(expected)

        found = input_stream.read()
        assert found==expected, filename
        input_stream.close()

def test_io_close_input_stream(fs):

    issue_708_workaround()

    with open(WOMBAT_TEX, 'w') as f:
        f.write('one\ntwo\nthree')

    fake_stdin = FakeStdin(['alpha', 'beta', 'gamma'])
    old_stdin = sys.stdin
    sys.stdin = fake_stdin

    doc = yex.Document()

    def next_bit():
        found = doc[r'_inputs;1'].read()
        result = ''.join([x.ch for x in found
                if isinstance(x, (yex.parse.Letter, yex.parse.Other))])
        return result

    assert next_bit()=='alpha'

    doc[r'_inputs;1'].open(
            filename = WOMBAT_TEX,
            )

    assert next_bit()=='one'
    assert next_bit()=='two'

    doc[r'_inputs;1'].close()

    assert next_bit()=='beta'

    sys.stdin = old_stdin

def test_terminal_is_always_eof():
    doc = yex.Document()
    terminal = doc['_inputs;-1']
    assert terminal.eof
