from mex.put import put

def test_put_simple():
    s = 'The quick brown fox jumps over the lazy dog.'

    assert put(s)==s
