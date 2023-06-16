import yex
from test import *

def test_ignorespaces():
    for (source, expected) in [
            (r'\ignorespaces1', '1'),
            (r'\ignorespaces 2', '2'),
            (r'\ignorespaces       3', '3'),
            ]:
        doc = yex.Document()
        e = doc.open(source)
        found = e.next(level='executing')
        assert isinstance(found, yex.parse.Other), source
        assert found.ch==expected, source
