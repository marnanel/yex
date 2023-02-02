from test import *

def test_countdef():
    string = r'\count28=17 '+\
            r'\countdef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18'+\
            r'\the\count28'
    assert run_code(string,
            find = "chars") == '1718'

def test_dimendef():
    string = r'\dimen28=17.0pt'+\
            r'\dimendef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18.0pt'+\
            r'\the\dimen28'
    assert run_code(string,
            find = "chars") == '17.0pt18.0pt'

def test_skipdef():
    string = r'\skip28=17.0pt plus 1.0pt minus 2.0pt'+\
            r'\skipdef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18.0pt plus 3.0pt minus 4.0pt'+\
            r'\the\skip28'
    assert run_code(string,
            find = "chars") == (
                    '17.0pt plus 1.0pt minus 2.0pt' # no space here
                    '18.0pt plus 3.0pt minus 4.0pt')

def test_muskipdef():
    string = r'\muskip28=17.0pt plus 1.0pt minus 2.0pt'+\
            r'\muskipdef\chapno=28 '+\
            r'\the\chapno'+\
            r'\chapno=18.0pt plus 3.0pt minus 4.0pt'+\
            r'\the\muskip28'
    assert run_code(string,
            find = "chars") == (
                    '17.0pt plus 1.0pt minus 2.0pt' # no space here
                    '18.0pt plus 3.0pt minus 4.0pt')

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
