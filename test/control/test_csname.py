import yex
from test import *
import pytest

DEF_TEX = r"\def\TeX{" + TEX_LOGO + "}"

def test_csname_p40_simple():

    doc = yex.Document()

    found = run_code(
            setup=DEF_TEX,
            call=r'\csname TeX\endcsname',
            doc=doc,
            find='saw',
            )

    assert isinstance(found[0], yex.box.HBox)

def test_csname_p40_nontokens():

    doc = yex.Document()

    with pytest.raises(yex.exception.YexError):
        found = run_code(
                setup=DEF_TEX,
                call=r'\csname\TeX\endcsname',
                doc=doc,
                )

def test_csname_p40_with_string():

    doc = yex.Document()

    found = run_code(
            setup=DEF_TEX,
            call=r'\csname\string \TeX\endcsname',
            doc=doc,
            find = 'saw',
            )

    assert isinstance(found[0], yex.parse.Control)
    assert found[0].ch==r'\\TeX'

def test_csname_creates_control():

    doc = yex.Document()

    assert doc.get(r'\\wombat', default=None)==None

    found = run_code(
            call=r'\csname\string \wombat\endcsname',
            doc=doc,
            find = 'saw',
            )

    assert isinstance(found[0], yex.parse.Control)
    assert found[0].ch==r'\\wombat'

    assert isinstance(
            doc.get(r'\wombat'),
            yex.control.Relax)