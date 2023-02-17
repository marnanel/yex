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
            ('the letter S', 0),
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
    r"""
    Tests `\expandafter\expandafter\expandafter`.

    The sequence here is:
        1. Expandafter1 saves Expandafter2 and runs Expandafter3.
        2. Expandafter3 saves \brackets and runs \greeting.
        3. \greeting provides the five-token string "spong".
        4. Expandafter3 adds \brackets back in front, so we now
            have "\brackets spong".
        5. Expandafter1 adds Expandafter2 back in front, so we now
            have "\expandafter\brackets spong".
        6. Expandafter2 now runs, saves \brackets, and runs "s", which
            produces "s". Thus we have "spong". It then puts \brackets
            back before it, so we have "\brackets s pong".
        7. This expands to "(s)pong".

        Useful reading:

        https://www.overleaf.com/learn/latex/Articles/\
                How_does_%5Cexpandafter_work%3A_A_detailed_\
                study_of_consecutive_%5Cexpandafter_commands
    """
    doc = yex.Document()

    found = run_code(
            doc=doc,
            setup=(
                r'\def\brackets#1{(#1)}'
                r'\def\greeting{spong}'
                ),
            call=(
                r'\expandafter\expandafter\expandafter\brackets\greeting'
                ),
            find=['ch', 'expander'],
            )

    assert found['ch']=='(s)pong'
    assert found['expander'].pushback.group_depth==0
