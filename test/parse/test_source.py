import mex.parse.source

def _test_file(fs, contents,
        name="wombat.txt"):
    fs.create_file(name,
            contents = contents)

    result = mex.parse.source.Source(
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
