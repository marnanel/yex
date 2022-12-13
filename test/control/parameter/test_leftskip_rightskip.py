import yex
from test import *

def test_leftskip_rightskip():

    doc = yex.Document()

    found = run_code(
            r"""
\hsize=6cm
\parfillskip=0cm
\parindent=0cm
\pretolerance=1000000

\leftskip=0pt\rightskip=0pt Welwyn Garden City

\leftskip=1pt\rightskip=0pt Welwyn Garden City

\leftskip=0pt\rightskip=1pt Welwyn Garden City

\leftskip=1pt\rightskip=1pt Welwyn Garden City
            """,
            doc=doc,
            mode='vertical',
            output='dummy',
            find='list')
    doc.save()

    vboxes = [v for v in found if isinstance(v, yex.box.VBox)]
    assert [len(v) for v in vboxes]==[1] * 4

    hboxes = [h[0] for h in vboxes]
    assert [len(h) for h in hboxes]==[9] * 4

    assert [h[0].name for h in hboxes]==[r'\leftskip'] * 4
    assert [float(h[0].width) for h in hboxes]==[0, 1, 0, 1]

    assert [h[-1].name for h in hboxes]==[r'\rightskip'] * 4
    assert [float(h[-1].width) for h in hboxes]==[0, 0, 1, 1]
