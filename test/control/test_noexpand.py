def test_noexpand():
    assert run_code(r"\noexpand1",
            find='ch',
            )=="1"

    doc = Document()
    string = (
            r"\def\b{B}"
            r"\edef\c{1\b2\noexpand\b3\b}"
            )
    run_code(string,
            find='chars',
            doc=doc)

    assert ''.join([
        repr(x) for x in doc[r'\c'].definition
        if not x.category==x.INTERNAL
        ])==r'[1][B][2]\b[3][B]'
