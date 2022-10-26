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

    assert doc.pushback.group_depth==0

    run_code(
            doc=doc,
            setup=(
                r'\def\spong{spong}'
                ),

             call=(
                r'\uppercase\expandafter{\spong\spong}le '
                ),
            )

    assert doc.pushback.group_depth==0

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
