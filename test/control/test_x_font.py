import yex
from test import *
import pytest

def test_x_font(yex_test_fs):

    doc = yex.Document()

    initial = doc['_font']
    assert isinstance(initial, yex.font.Default)
    assert id(doc.font)==id(initial)

    nullfont = yex.font.Nullfont()

    doc['_font'] = nullfont
    assert id(doc['_font'])==id(nullfont)
    assert id(doc.font)==id(nullfont)

    doc['_font'] = initial
    assert id(doc['_font'])==id(initial)
    assert id(doc.font)==id(initial)

    doc['_font'] = 'cmr10'
    assert isinstance(doc['_font'], yex.font.Tfm)
    assert id(doc['_font'])==id(doc.font)
    assert doc['_font'].name == 'cmr10'

    with pytest.raises(TypeError):
        doc['_font'] = 123456
