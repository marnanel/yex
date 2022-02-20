import mex.parse.source

def _test_file(fs, contents,
        name="wombat.txt"):
    fs.create_file(name,
            contents = contents)

    result = mex.parse.source.FileSource(
            source = open(name, 'r'),
            name = name,
            )

    return result

def test_source_simple(fs):
    source = _test_file(fs, "hello world")
    contents = ''

    for t in source:
        contents += t

    assert contents == "hello world"

def test_source_location(fs):
    source = _test_file(fs, """this
    is

    fun""")

    expected = [
            ('t', 1, 1),
            ('h', 1, 2),
            ('i', 1, 3),
            ('s', 1, 4),
            ('\n', 1, 5),
            (' ', 2, 1),
            (' ', 2, 2),
            (' ', 2, 3),
            (' ', 2, 4),
            ('i', 2, 5),
            ('s', 2, 6),
            ('\n', 2, 7),
            ('\n', 3, 1),
            (' ', 4, 1),
            (' ', 4, 2),
            (' ', 4, 3),
            (' ', 4, 4),
            ('f', 4, 5),
            ('u', 4, 6),
            ('n', 4, 7),
            ]

    for found, (wanted, line, column) in zip(source, expected):
        assert found==wanted
        assert source.line_number==line
        assert source.column_number==column
        assert source.location==(source, line, column)
        assert str(source)=='wombat.txt:%4d:%5d' % (column, line,)

def test_null_source():
    source = mex.parse.source.NullSource()

    result = ''
    for t in source:
        result += t

    assert result==''
