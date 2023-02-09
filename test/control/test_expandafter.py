import yex
from test import *

def test_expandafter_issue110():
    assert run_code(
            setup=(
                r'\def\spong{spong}'
                ),

            # We double up \spong to ensure that it's not working
            # merely because of pushback from the parser.
            #
            # The "le" at the end tests whether \uppercase has picked up
            # where to stop.
            call=(
                r'\uppercase{\spong\spong}le '
                r'\uppercase\expandafter{\spong\spong}le '
                ),
            find='ch',
            )=='spongspongle SPONGspongle'

def test_expandafter_first_token_is_opening_curly_bracket():
    assert run_code(
            setup=(
                r'\def\spong{spong}'
                ),
            call=(
                r'\def\spong{spong}'
                r'\uppercase\expandafter{\spong\spong}le'
                ),
            find='ch',
            )=='SPONGspongle'

def test_expandafter_depth():
    doc = yex.Document()
    e = doc.open(
                r'\def\spong{spong}'
                r'\uppercase\expandafter{\spong\spong}le ',
                level='executing',
                on_eof='exhaust',
                )

    assert e.pushback.group_depth==0

    found = [(repr(t), e.pushback.group_depth) for t in e]

    assert found == [
            ('begin-group character ', 1),
            ('the letter S', 1),
            ('end-group character ', 0),
            ('the letter P', 0),
            ('the letter O', 0),
            ('the letter N', 0),
            ('the letter G', 0),
            ('the letter s', 0),
            ('the letter p', 0),
            ('the letter o', 0),
            ('the letter n', 0),
            ('the letter g', 0),
            ('the letter l', 0),
            ('the letter e', 0),
            ('blank space  ', 0),
            ]

def test_expandafter_multiple_times():
    doc = yex.Document()

    assert run_code(
            doc=doc,
            setup=(
                r'\def\brackets#1{(#1)}'
                r'\def\greeting{spong}'
                ),
            call=(
                r'\expandafter\expandafter\expandafter\brackets\greeting'
                ),
            find='ch',
            )=='(s)pong'
