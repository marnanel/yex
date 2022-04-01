def test_countdef():
    string = r'\count28=17 '+\
            r'\countdef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18'+\
            r'\the\count28'
    assert run_code(string,
            find = "chars") == '1718'

def test_dimendef():
    string = r'\dimen28=17pt'+\
            r'\dimendef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18pt'+\
            r'\the\dimen28'
    assert run_code(string,
            find = "chars") == '17pt18pt'

def test_skipdef():
    string = r'\skip28=17pt plus 1pt minus 2pt'+\
            r'\skipdef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18pt plus 3pt minus 4pt'+\
            r'\the\skip28'
    assert run_code(string,
            find = "chars") == '17pt plus 1pt minus 2pt18pt plus 3pt minus 4pt'

def test_muskipdef():
    string = r'\muskip28=17pt plus 1pt minus 2pt'+\
            r'\muskipdef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18pt plus 3pt minus 4pt'+\
            r'\the\muskip28'
    assert run_code(string,
            find = "chars") == '17pt plus 1pt minus 2pt18pt plus 3pt minus 4pt'

def test_toksdef():
    string = (
            r'\toks28={Yes, we have no bananas}'
            r'\toksdef\bananas=28 '
            r'\the\bananas'
            r'\bananas={delicious and yellow}'
            r'\the\toks28'
            )
    assert run_code(string,
            find = "chars") == (
                    'Yes, we have no bananas'
                    'delicious and yellow'
                    )
