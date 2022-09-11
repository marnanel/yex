import io
import logging
import yex
from test import *

logger = logging.getLogger('yex.general')

def _test_file(fs, contents,
        name="wombat.txt"):
    fs.create_file(name,
            contents = contents)

    result = yex.parse.source.FileSource(
            f = open(name, 'r'),
            name = name,
            )

    return result

def _swallow(source):
    result = ''

    for t in source:
        if t is None:
            break
        result += str(t)

    return result.rstrip('\r')

def test_source_simple(fs):
    source = _test_file(fs, "hello world")
    assert _swallow(source) == "hello world"

def test_source_pushback():
    with io.StringIO("ovine") as f:
        s = yex.parse.source.FileSource(f)

        s.push('b')

        assert _swallow(s)=='bovine'

    with io.StringIO("arial") as f:
        s = yex.parse.source.FileSource(f)

        s.push('secret')

        assert _swallow(s)=='secretarial'

    with io.StringIO("wombat") as f:
        s = yex.parse.source.FileSource(f)

        s.push(None)

        assert _swallow(s)=='wombat'

    with io.StringIO("roblem") as f:
        s = yex.parse.source.FileSource(f)

        s.push([chr(x) for x in range(ord('n'), ord('q'))])

        assert _swallow(s)=='noproblem'

def test_source_location(fs):

    expected = [
            ('t', 1, 1),
            ('h', 1, 2),
            ('i', 1, 3),
            ('s', 1, 4),
            ('\r', 1, 5),
            (' ', 2, 1),
            (' ', 2, 2),
            (' ', 2, 3),
            (' ', 2, 4),
            ('i', 2, 5),
            ('s', 2, 6),
            ('\r', 2, 7),
            ('\r', 3, 1),
            (' ', 4, 1),
            (' ', 4, 2),
            (' ', 4, 3),
            (' ', 4, 4),
            ('f', 4, 5),
            ('u', 4, 6),
            ('n', 4, 7),
            ]

    def _try(source, flavour, name):
        for found, (wanted, line, column) in zip(source, expected):
            line_name = f'{flavour}:{line}:{column}'
            assert found==wanted, line_name
            assert source.line_number==line, line_name
            assert source.column_number==column, line_name
            assert source.location.filename==name, line_name
            assert source.location.line==line, line_name
            assert source.location.column==column, line_name

            assert str(source)=='[%s;%s;l=%d;c=%d]' % (
                    flavour, name, line, column,), line_name
            assert str(source.location)=='%s:%d:%d' % (
                    name, line, column,), line_name

    for newline in ['\r', '\n', '\r\n']:

        string = f"this{newline}    is{newline}{newline}    fun"

        filesource = _test_file(fs, string)
        _try(filesource, 'FileSource', 'wombat.txt')
        fs.remove_object('wombat.txt')

        stringsource = yex.parse.source.StringSource(string)
        _try(stringsource, 'StringSource', '<str>')

def test_source_currentline():
    string1 = "This is a line 1\r"
    string2 = "2 And this is another\r"
    joined = string1+string2

    source = yex.parse.source.StringSource(joined)

    for t in source:
        if t is None:
            break

        if t=='1':
            assert source.current_line==string1
        elif t=='2':
            assert source.current_line==string2

def test_source_push_partway(fs):
    source = _test_file(fs, "dogs")

    assert next(source)=='d'
    assert source.peek()=='o'
    assert source.peek()=='o'
    assert next(source)=='o'
    source.push('i')
    assert source.peek()=='i'
    assert next(source)=='i'
    assert next(source)=='g'
    source.push('t')
    source.push('a')
    source.push('c')
    assert source.peek()=='c'
    assert next(source)=='c'
    assert next(source)=='a'
    assert next(source)=='t'
    assert next(source)=='s'
    assert next(source)=='\r'
    assert next(source) is None

def test_source_rstrip_simple(fs):
    source = _test_file(fs,
            contents="fred       \rbasset")

    assert _swallow(source)=='fred\rbasset'

def test_source_rstrip_with_tab(fs):
    source = _test_file(fs,
            contents="fred\t       \rbasset")

    assert _swallow(source)=='fred\t\rbasset'

def test_source_nullsource():
    source = yex.parse.source.NullSource()

    result = ''
    for t in source:
        assert t is None
        break

def test_source_stringsource():
    string = 'hello world'
    source = yex.parse.source.StringSource(
            string,
            )

    assert _swallow(source)==string

def test_source_listsource():

    class Omba:
        def __str__(self):
            return 'omba'

    contents = ['w', Omba(), 't']
    source = yex.parse.source.ListSource(
            contents,
            )

    assert _swallow(source)=='wombat'

def test_location_serialise():

    something = yex.parse.Location(
            filename = 'banana.tex',
            line = 23,
            column = 100,
            )

    serial = something.__getstate__()

    assert serial == 'banana.tex:23:100'

    assert yex.parse.Location.from_serial(serial)==something

def test_source_exhaust_at_eol():
    STRING = 'A\rBCD\rEF\rG\r'

    found = []
    for j in range(len(STRING)):
        source = yex.parse.source.StringSource(STRING)

        found.append('')
        for i, t in enumerate(source):
            if t is None:
                break
            if i==j:
                logger.debug("setting exhaust_at_eol now")
                source.exhaust_at_eol = True

            if t=='\r':
                found[-1] += ' '
            else:
                found[-1] += str(t)

    assert found==[
            'A ',
            'A ',
            'A BCD ',
            'A BCD ',
            'A BCD ',
            'A BCD ',
            'A BCD EF ',
            'A BCD EF ',
            'A BCD EF ',
            'A BCD EF G ',
            'A BCD EF G ',
            ]
