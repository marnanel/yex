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

\leftskip=0cm\rightskip=0cm Welwyn Garden City

\leftskip=1cm\rightskip=0cm Welwyn Garden City

\leftskip=0cm\rightskip=1cm Welwyn Garden City

\leftskip=1cm\rightskip=1cm Welwyn Garden City
            """,
            doc=doc,
            mode='vertical',
            output='dummy',
            find='ch')
    doc.save()

    assert found=='obviously not'
