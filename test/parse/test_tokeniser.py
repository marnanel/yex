from mex.parse import Tokeniser
import mex.state
from .. import *

def _check_line_status(string):
    """
    Creates a Tokeniser, and asserts that it's in line status "N".
    Then, for every Token produced by tokenising "string", adds
    the token's "ch" property and the Tokeniser's line status
    to the result string. Finally, it returns the result string.
    """
    s = mex.state.State()
    t = Tokeniser(state=s, source=string)

    result = ''
    for token in t:
        if token is None: break
        result += t.line_status + token.ch

    return result

def _test_tokeniser(
        text,
        expected,
        s = None,
        ):

    if s is None:
        s = mex.state.State()

    result = []

    t = Tokeniser(state=s, source=text)
    for item in t:
        if item is None:
            break
        result.append(str(item))

    if result[-1]=='    32 ( ) Space':
        # extra \r at EOF
        result = result[:-1]

    assert result == expected
    return result

def test_tokeniser_simple():
    assert _check_line_status(
            "Aa Bb\nCc"
            )=="NAMaM SBMbM NCMcM "

def test_tokeniser_comment():
    assert _check_line_status(
            "What% is this\rso?"
            )=="NWMhMaMtNsMoM?M "

def test_tokeniser_simple_create():
    s = mex.state.State()
    t = Tokeniser(s, [])
    assert t is not None

def test_tokeniser_simple_text():

    _test_tokeniser(
            text = "fred123$",
    expected = [
        '   102 (f) Letter',
        '   114 (r) Letter',
        '   101 (e) Letter',
        '   100 (d) Letter',
        '    49 (1) Other character',
        '    50 (2) Other character',
        '    51 (3) Other character',
        '    36 ($) Math shift',
        ],
    )

def test_tokeniser_push_back():
    _test_tokeniser(
            text = r"\loop\iftrue",
    expected = [
        r'\loop',
        r'\iftrue',
        ],
    )

def test_tokeniser_push_back_string():
    s = mex.state.State()

    result = ''
    done_the_push = False
    string = 'ab'
    t = Tokeniser(state=s, source=string)

    for c in t:
        if c is None:
            break
        result += c.ch

        if not done_the_push:
            t.push("hey")
            done_the_push = True

    assert result=='aheyb '

def test_tokeniser_caret():

    s = mex.state.State()
    s['catcode00'] = 11

    _test_tokeniser(
            text = "a^^@b",
            expected = [
                '    97 (a) Letter',
                '     0     Letter',
                '    98 (b) Letter',
                ],
            s = s,
            )

    _test_tokeniser(
            text = "a^b",
            expected = [
                '    97 (a) Letter',
                '    94 (^) Superscript',
                '    98 (b) Letter',
                ],
            )

    _test_tokeniser(
            text = "a^^6fb",
            expected = [
                '    97 (a) Letter',
                '   111 (o) Letter',
                '    98 (b) Letter',
                ],
            )

    _test_tokeniser(
            text = "a^^6=b",
            expected = [
                '    97 (a) Letter',
                '   118 (v) Letter',
                '    61 (=) Other character',
                '    98 (b) Letter',
                ],
            )

    _test_tokeniser(
            text = "a^^Ab",
            expected = [
                '    97 (a) Letter',
                '     1     Other character',
                '    98 (b) Letter',
                ],
            )

def test_tokeniser_active_characters():
    _test_tokeniser(
            text = "R.~J. Drofnats",
            expected = [
                '    82 (R) Letter',
                '    46 (.) Other character',
                '   126 (~) Active character',
                '    74 (J) Letter',
                '    46 (.) Other character',
                '    32 ( ) Space',
                '    68 (D) Letter',
                '   114 (r) Letter',
                '   111 (o) Letter',
                '   102 (f) Letter',
                '   110 (n) Letter',
                '    97 (a) Letter',
                '   116 (t) Letter',
                '   115 (s) Letter',
                ],
            )

def test_tokeniser_eat_optional_spaces():
    s = mex.state.State()
    text = 'a         b'
    t = Tokeniser(state=s, source=text)

    result = ''

    for c in t:
        if c is None:
            break
        result += c.ch
        t.eat_optional_spaces()

    assert result=='ab'

def test_tokeniser_eat_optional_equals():
    s = mex.state.State()

    text = 'a         =b'

    t = Tokeniser(state=s, source=text)

    result = ''

    for c in t:
        if c is None:
            break
        result += c.ch
        t.eat_optional_equals()

    assert result=='ab'

def test_tokeniser_optional_string():
    s = mex.state.State()

    text = r'\red papaya\green'

    result = []

    t = Tokeniser(state=s, source=text)

    for c in t:
        result.append(
                (repr(c), t.optional_string("paya")),
                )
        if c is None:
            break

    assert result==[
            (r'\red', False),
            (r'[p]', False),
            (r'[a]', True),
            (r'\green', False),
            ('[  Space]', False),
            ('None', False),
            ]

def test_ascii_lookup():
    """
    Tests the various ways of getting ASCII code information.

    See the TeXbook, p43f.
    """
    assert run_code(r'\char98',   find='chars')=='b'
    assert run_code(r"\char'142", find='chars')=='b'
    assert run_code(r'\char"62',  find='chars')=='b'
