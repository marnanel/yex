def test_mathchardef():
    string = r'\mathchardef\sum="1350'
    yex.put.put(string)
    # XXX This does nothing useful yet,
    # XXX but we have the test here to make sure it parses
