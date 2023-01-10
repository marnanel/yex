import pytest
from test import *
import yex

def test_tracingoutput(capsys):

    def split(s):
        # This only exists to make comparisons easier if the test fails
        return s.split('\n')

    doc = yex.Document()

    run_code(
            call=EXAMPLE_DOCUMENT,
            doc=doc,
            mode='vertical',
            )

    doc.save()

    assert split(capsys.readouterr().out)==split(EXPECTED_SHOWBOX)

EXAMPLE_DOCUMENT = r"""\hsize=150pt
\hyphenpenalty=10000
\exhyphenpenalty=10000
\clubpenalty=50
\widowpenalty=50
\tracingoutput=1
\showboxbreadth=1000
\pretolerance=10000
\topskip=10pt
\baselineskip=12pt
\rightskip=0pt
\parfillskip=0pt plus 1fil
\parskip=0pt plus 1pt

We need very much a name to describe a cultivator of science in general.

I should incline to call him a scientist."""

EXPECTED_SHOWBOX = r"""\vbox(667.20255+0.0)x150.0
.\vbox(0.0+0.0)x150.0, glue set 14.0fil
..\glue -22.5
..\hbox(8.5+0.0)x150.0, glue set 150.0fil
...\vbox(8.5+0.0)x0.0
...\glue 0.0 plus 1.0fil
..\glue 0.0 plus 1.0fil minus 1.0fil
.\vbox(643.20255+0.0)x150.0, glue set 585.20255fill
..\glue(\topskip) 3.05556
..\hbox(6.94444+1.94444)x150.0, glue set - 0.46252
...\hbox(0.0+0.0)x20.0
...\tenrm W
...\kern-0.83334
...\tenrm e
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm n
...\tenrm e
...\tenrm e
...\tenrm d
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm v
...\kern-0.27779
...\tenrm e
...\tenrm r
...\tenrm y
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm m
...\kern-0.27779
...\tenrm u
...\tenrm c
...\kern-0.27779
...\tenrm h
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm a
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm n
...\tenrm a
...\tenrm m
...\tenrm e
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm t
...\tenrm o
...\glue(\rightskip) 0.0
..\penalty 50
..\glue(\baselineskip) 3.11111
..\hbox(6.94444+0.0)x150.0, glue set 0.54665
...\tenrm d
...\tenrm e
...\tenrm s
...\tenrm c
...\tenrm r
...\tenrm i
...\tenrm b
...\kern0.27779
...\tenrm e
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm a
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm c
...\tenrm u
...\tenrm l
...\tenrm t
...\tenrm i
...\tenrm v
...\kern-0.55556
...\tenrm a
...\tenrm t
...\tenrm o
...\tenrm r
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm o
...\tenrm f
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm s
...\tenrm c
...\tenrm i
...\tenrm e
...\tenrm n
...\tenrm c
...\tenrm e
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm i
...\tenrm n
...\glue(\rightskip) 0.0
..\penalty 50
..\glue(\baselineskip) 5.05556
..\hbox(6.94444+1.94444)x150.0, glue set 116.08327fil
...\tenrm g
...\tenrm e
...\tenrm n
...\tenrm e
...\tenrm r
...\tenrm a
...\tenrm l
...\tenrm .
...\penalty 10000
...\glue(\parfillskip) 0.0 plus 1.0fil
...\glue(\rightskip) 0.0
..\glue(\parskip) 0.0 plus 1.0
..\glue(\baselineskip) 3.11111
..\hbox(6.94444+0.0)x150.0, glue set 0.41116
...\hbox(0.0+0.0)x20.0
...\tenrm I
...\glue 3.33333 plus 1.66498 minus 1.11221
...\tenrm s
...\tenrm h
...\tenrm o
...\tenrm u
...\tenrm l
...\tenrm d
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm i
...\tenrm n
...\tenrm c
...\tenrm l
...\tenrm i
...\tenrm n
...\tenrm e
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm t
...\tenrm o
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm c
...\tenrm a
...\tenrm l
...\tenrm l
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm h
...\tenrm i
...\tenrm m
...\glue 3.33333 plus 1.66666 minus 1.11111
...\tenrm a
...\glue(\rightskip) 0.0
..\penalty 100
..\glue(\baselineskip) 5.32141
..\hbox(6.67859+0.0)x150.0, glue set 111.83328fil
...\tenrm s
...\tenrm c
...\tenrm i
...\tenrm e
...\tenrm n
...\kern-0.27779
...\tenrm t
...\tenrm i
...\tenrm s
...\tenrm t
...\tenrm .
...\penalty 10000
...\glue(\parfillskip) 0.0 plus 1.0fil
...\glue(\rightskip) 0.0
..\hbox(0.0+0.0)x150.0
..\glue 0.0 plus 1.0fill
.\glue(\baselineskip) 17.55556
.\hbox(6.44444+0.0)x150.0, glue set 72.5fil
..\glue 0.0 plus 1.0fil minus 1.0fil
..\tenrm 1
..\glue 0.0 plus 1.0fil minus 1.0fil
"""
