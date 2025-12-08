from test import *
import pytest
from yex.parse.tokeniser import _caret_eater as ce

def test_caret_eater():

    def _test_ce(text, expected):
        found = ''
        for c in ce(iter(text)):
            found += c

        assert found==expected, text

    _test_ce(
            text = "a^^@b",
            expected = 'a\x00b',
            )

    _test_ce(
            text = "a^b",
            expected = 'a^b',
            )

    _test_ce(
            text = "a^^6fb",
            expected = 'aob',
            )

    _test_ce(
            text = "a^^6=b",
            expected = 'av=b',
            )

    _test_ce(
            text = "a^^Ab",
            expected = 'a\x01b',
            )

    _test_ce(
            text = r"\d^^6fg",
            expected = r'\dog',
            )
