from test import *

@yex_control_test([r'\countdef', r'\the'])
def test_countdef():
    string = r'\count28=17 '+\
            r'\countdef\chapno=28 '+\
            r'(\the\chapno)'+\
            r'\chapno=18'+\
            r'(\the\count28)'
    assert run_code(string,
            find = "chars") == '(17)(18)'

@yex_control_test([r'\dimendef', r'\the'])
def test_dimendef():
    string = r'\dimen28=17.0pt'+\
            r'\dimendef\chapno=28 '+\
            r'(\the\chapno)'+\
            r'\chapno=18.0pt'+\
            r'(\the\dimen28)'
    assert run_code(string,
            find = "chars") == '(17.0pt)(18.0pt)'

@yex_control_test([r'\skipdef', r'\the'])
def test_skipdef():
    string = r'\skip28=17.0pt plus 1.0pt minus 2.0pt'+\
            r'\skipdef\chapno=28 '+\
            r'(\the\chapno)'+\
            r'\chapno=18.0pt plus 3.0pt minus 4.0pt'+\
            r'(\the\skip28)'
    assert run_code(string,
            find = "chars") == (
                    '(17.0pt plus 1.0pt minus 2.0pt)' # no space here
                    '(18.0pt plus 3.0pt minus 4.0pt)')

@yex_control_test([r'\muskipdef', r'\the'])
def test_muskipdef():
    string = r'\muskip28=17.0mu plus 1.0mu minus 2.0mu'+\
            r'\muskipdef\chapno=28 '+\
            r'(\the\chapno)'+\
            r'\chapno=18.0mu plus 3.0mu minus 4.0mu'+\
            r'(\the\muskip28)'
    assert run_code(string,
            find = "chars") == (
                    '(17.0mu plus 1.0mu minus 2.0mu)' # no space here
                    '(18.0mu plus 3.0mu minus 4.0mu)')

@yex_control_test([r'\the', r'\toks', r'\toksdef'])
def test_toksdef():
    string = (
            r'\toks28={Yes, we have no bananas}'
            r'\toksdef\bananas=28 '
            r'(\the\bananas)'
            r'\bananas={delicious and yellow}'
            r'(\the\toks28)'
            )
    assert run_code(string,
            find = "chars") == (
                    '(Yes, we have no bananas)'
                    '(delicious and yellow)'
                    )
