import pytest
import string
import yex
from test import *

def test_io_streams_exist():
    s = yex.document.Document()
    assert s['_input_streams;-1'] is not None
    assert s['_input_streams;0'] is not None
    assert s['_input_streams;1'] is not None
    assert s['_input_streams;15'] is not None
    assert s['_input_streams;16'] is not None

    assert s['_output_streams;-1'] is not None
    assert s['_output_streams;0'] is not None
    assert s['_output_streams;1'] is not None
    assert s['_output_streams;15'] is not None
    assert s['_output_streams;16'] is not None

def test_io_write_to_terminal(capsys):

    s = yex.document.Document()
    string = 'Hello world\rHurrah'

    terminal = s['_output_streams;16']
    terminal.write(string)
    result = capsys.readouterr().out

    assert result==string.replace('\r', '\n')

def test_io_write_to_file(fs):
    assert False

def test_io_write_to_log_but_not_terminal(fs):
    assert False

def test_io_read_from_terminal():
    assert False

TEST_DATA = r"""This contains } some number { of
matching } lines
But\par if there is { some set} of } braces
Then it will { read
onto the } next line as well"""

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

    doc = yex.Document()

    with open('fred.tex', 'w') as fred:
        fred.write(TEST_DATA)

    input_stream = yex.io.InputStream(
            doc = doc,
            filename = 'fred.tex',
            )
    assert not input_stream.eof

    for expect_eof, line in [
            (False, ['This contains']),
            (False, ['matching']),
            (False, ['But',
                yex.parse.Control(r'par', doc=doc, location=None),
                'if there is ',
                yex.parse.Control(r'par', doc=doc, location=None),
                'or ',
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
            ]:

        expected = _munge_tokens(line,
                add_space = not expect_eof)

        found = input_stream.read()

        assert expected==found, line
        assert input_stream.eof == expect_eof

    input_stream.close()
    assert input_stream.eof

def test_io_read_from_closed_file(fs):
    doc = yex.Document()

    with open('fred.tex', 'w') as fred:
        fred.write(TEST_DATA)

    input_stream = yex.io.InputStream(
            doc = doc,
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
            filename = 'gronda.tex',
            )

    assert input_stream.eof
    found = input_stream.read()
    assert found is None

def test_io_read_supplies_file_extension(fs):

    doc = yex.Document()

    # Workaround for https://github.com/jmcgeheeiv/pyfakefs/issues/708
    open.__self__.skip_names.remove('io')

    with open('wombat.tex', 'w') as f:
        f.write('wombat')
    with open('spong.html', 'w') as f:
        f.write('spong')

    for filename, expected in [
            ('wombat', 'wombat'),
            ('wombat.tex', 'wombat'),
            ('wombat.html', None),
            ('spong', None),
            ('spong.html', 'spong'),
            ]:

        input_stream = yex.io.InputStream(
                doc = doc,
                filename = filename,
                )

        expected = _munge_tokens(expected)

        found = input_stream.read()
        assert found==expected, filename
        input_stream.close()
