from test import *
import yex

EXAMPLE_DOCUMENT = r"""
\hsize=130pt
\parindent=0pt
\pretolerance=5000
\showboxbreadth=1000

\interlinepenalty=10
\brokenpenalty=20
\clubpenalty=40
\widowpenalty=80
\displaywidowpenalty=160

As I went a-walking one morning in spring,
I met with three travellers in an old country lane.

One was an old man.

The second, a maid.

The third was a young boy who smiled as he said:

With the wind in the wil\discretionary{-}{}{}lows
and the stars in the sky, we've a bright
sun to warm us wherever we lie.
We have bread and fishes and a jug of
red wine to share on our journey with all of mankind.
"""

def test_clubpenalty(capsys):

    INTERLINE = 10     # all lines have this
    BROKEN = 20        # lines broken after a hyphen ("wil"-"lows")
    CLUB = 40          # between the first and second lines of a para
    WIDOW = 80         # between the penultimate and last lines
    DISPLAYWIDOW = 80  # like WIDOW, but before maths; we don't use this yet

    EXPECTED = [
            CLUB+INTERLINE,
                INTERLINE,
                INTERLINE,
                WIDOW+INTERLINE,

            CLUB+WIDOW+INTERLINE,

            CLUB+WIDOW+INTERLINE,

            CLUB+INTERLINE,
                WIDOW+INTERLINE,

            CLUB+BROKEN+INTERLINE,
                INTERLINE,
                INTERLINE,
                INTERLINE,
                INTERLINE,
                INTERLINE,
                WIDOW+INTERLINE,
            ]

    doc = yex.Document()

    results = run_code(
            call=EXAMPLE_DOCUMENT,
            doc=doc,
            mode='vertical',
            output='dummy',
            find='list',
            )

    doc.save()

    found = [penalty.demerits for penalty in results
                if isinstance(penalty, yex.box.Penalty)]

    assert found==EXPECTED
