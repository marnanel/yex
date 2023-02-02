import yex
from test import *

def test_leftskip_rightskip():

    hboxes = run_code(
            r"""
\hsize=6cm
\parfillskip=0cm
\parindent=0cm
\pretolerance=1000000

\leftskip=2pt\rightskip=2pt Welwyn Garden City

\leftskip=1pt\rightskip=2pt Welwyn Garden City

\leftskip=2pt\rightskip=1pt Welwyn Garden City

\leftskip=1pt\rightskip=1pt Welwyn Garden City
            """,
            mode='vertical',
            output='dummy',
            find='hboxes')

    assert [len(h) for h in hboxes]==[10] * 4, hboxes

    assert [h[0].name for h in hboxes]==[r'\leftskip'] * 4, hboxes
    assert [float(h[0].width) for h in hboxes]==[2, 1, 2, 1], hboxes

    assert [h[-1].name for h in hboxes]==[r'\rightskip'] * 4, hboxes
    assert [float(h[-1].width) for h in hboxes]==[2, 2, 1, 1], hboxes

def test_leftskip_zero_is_absorbed():

    hboxes = run_code(
            r"""
\hsize=6cm
\parfillskip=0cm
\parindent=0cm
\pretolerance=1000000

\leftskip=1pt\rightskip=1pt Letchworth Garden City

\leftskip=0pt\rightskip=0pt Letchworth Garden City
            """,
            mode='vertical',
            output='dummy',
            find='hboxes')

    assert [len(h) for h in hboxes]==[10, 9], hboxes

    assert isinstance(hboxes[0][0], yex.box.Leader)
    assert hboxes[0][0].space==1

    assert isinstance(hboxes[0][-1], yex.box.Leader)
    assert hboxes[0][-1].space==1

    assert not isinstance(hboxes[1][0], yex.box.Leader)

    assert isinstance(hboxes[1][-1], yex.box.Leader)
    assert hboxes[1][-1].space==0
