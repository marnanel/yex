def run_code_the(string, doc=None, *args, **kwargs):

    if doc is None:
        doc = Document()

    seen = run_code(string,
            doc = doc,
            *args, **kwargs,
            find = 'saw',
            )

    result = ''
    for c in seen:
        if isinstance(c, yex.parse.Control):
            continue

        if isinstance(c, yex.parse.Token):
            if c.ch==32:
                assert c.category==10
            else:
                assert c.category==12

            result += c.ch

    return result

def test_the_count():
    string = r'\count20=177\the\count20'
    assert run_code_the(string) == '177'

def test_the_dimen():
    string = r'\dimen20=20pt\the\dimen20'
    assert run_code_the(string) == '20pt'
