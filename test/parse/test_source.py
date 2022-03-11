import io
import mex.parse.source

def _test_file(fs, contents,
        name="wombat.txt"):
    fs.create_file(name,
            contents = contents)

    result = mex.parse.source.FileSource(
            f = open(name, 'r'),
            name = name,
            )

    return result

def _swallow(source):
    result = ''

    for t in source:
        if t is None:
            break
        result += t

    return result

def test_source_simple(fs):
    source = _test_file(fs, "hello world")
    assert _swallow(source) == "hello world"

def test_source_pushback():
    with io.StringIO("ovine") as f:
        s = mex.parse.source.FileSource(f)

        s.push('b')

        assert _swallow(s)=='bovine'

    with io.StringIO("arial") as f:
        s = mex.parse.source.FileSource(f)

        s.push('secret')

        assert _swallow(s)=='secretarial'

    with io.StringIO("wombat") as f:
        s = mex.parse.source.FileSource(f)

        s.push(None)

        assert _swallow(s)=='wombat'

    with io.StringIO("roblem") as f:
        s = mex.parse.source.FileSource(f)

        s.push([chr(x) for x in range(ord('n'), ord('q'))])

        assert _swallow(s)=='noproblem'

def test_source_location(fs):
    source = _test_file(fs, """this
    is

    fun""")

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

    for found, (wanted, line, column) in zip(source, expected):
        line_name = f'{line}:{column}'
        assert found==wanted, line_name
        assert source.line_number==line, line_name
        assert source.column_number==column, line_name
        assert source.location==(source, line, column), line_name
        assert str(source)=='wombat.txt:%4d:%5d' % (column, line,), line_name

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
    source = mex.parse.source.NullSource()

    result = ''
    for t in source:
        assert t is None
        break

def test_source_stringsource():
    string = 'hello world'
    source = mex.parse.source.StringSource(
            string,
            )

    assert _swallow(source)==string
