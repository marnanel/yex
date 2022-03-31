import pytest
from test import *
import yex.parse

def test_newline_during_outer_single():
    # See the commit message for an explanation
    run_code(
        r"\outer\def\a#1{b}"
        r"\a\q %Hello world"
        "\r"
        "\r",
        find = 'ch',
        )

def test_expander_level():

    STRING = (
            r"A \iffalse B\fi C \count20 6 {D} \hbox{E}"
            )

    EXPECTED = [
            ('deep', [
                'A', ' ', r'\iffalse', 'B', r'\fi', 'C', ' ',
                r'\count', '2', '0', ' ', '6', ' ',
                '{', 'D', '}', ' ',
                r'\hbox', '{', 'E', '}',
                ' ']),

            ('reading', [
                'A', ' ', r'[\iffalse]', 'B', r'[\fi]', 'C', ' ',
                # \count is returned as a token because there is
                # no \count object as such (it's just a prefix)
                r'\count', '2', '0', ' ', '6', ' ',
                '{', 'D', '}', ' ',
                r'[\hbox]', '{', 'E', '}',
                ' ']),

            ('expanding', [
                'A', ' ', 'C', ' ',
                r'[\count20]', '6', ' ',
                '{', 'D', '}', ' ',
                r'[\hbox]', '{', 'E', '}',
                ' ']),

            ('executing', [
                'A', ' ', 'C', ' ',
                # \count20 has gone because it's been executed
                '{', 'D', '}', ' ',
                r'[\hbox:xxxx]',
                ' ']),

            ('querying', [
                'A', ' ', 'C', ' ',
                r'[\count20]', '6', ' ',
                '{', 'D', '}', ' ',
                r'[\hbox:xxxx]',
                ' ']),

            ]

    def sample(level):
        doc = yex.Document()
        t = yex.parse.Tokeniser(doc, STRING)
        e = yex.parse.Expander(t,
                level=level,
                on_eof=yex.parse.Expander.EOF_EXHAUST,
                )
        return e

    def _hbox_fix(n):
        # HBox objects have unpredictable str() values because they're
        # based on the id() value. So, to make comparison possible,
        # we replace the four unpredictable characters with xxxx.

        if len(n)==12 and n.startswith(r'[\hbox:') and n[-1]==']':
            return r'[\hbox:xxxx]'
        else:
            return n

    for level, expected in EXPECTED:
        e = sample(level=level)

        found = [_hbox_fix(str(t)) for t in e]

        assert found==expected, f"at level {level}"

def test_expander_invalid_level():
    doc = yex.Document()

    e = doc.open("", level="reading")

    with pytest.raises(yex.exception.YexError):
        e = doc.open("", level="dancing")

def test_expander_single_at_levels():

    for level in [
            'executing',
            'expanding',
            'reading',
            'deep',
            ]:
        doc = yex.Document()
        e = doc.open("{A{B}C}D")

        e = e.another(single=True, level=level,
                on_eof=e.EOF_EXHAUST)

        assert ' '.join([str(t) for t in e])=='A { B } C', f"at level {level}"

def test_expander_single_with_deep_pushback():
    # Regression test.

    for whether in [False, True]:
        doc = yex.Document()
        e = doc.open("{A{B}C}D")

        e = e.another(single=True, level="reading",
                on_eof=e.EOF_EXHAUST)

        result = []

        for t in e:
            result.append(str(t))

            if whether and str(t)=='A':
                brace = e.next(level="deep")
                assert str(brace)=='{'
                e.push(brace)
                # and this should not affect whether the outer single
                # is working

        assert result==['A', '{', 'B', '}', 'C'], f"pushback?=={whether}"
