import io
import pytest
from mex.state import State
from mex.parse import Token, Tokeniser, Expander
from mex.value import Number, Dimen, Glue
import mex.exception
from .. import *
import mex.put
import mex.box
import logging

general_logger = logging.getLogger('mex.general')

def test_glue_variable():

    VARIABLES = [
            "baselineskip",
            "lineskip",
            "parskip",
            "abovedisplayskip",
            "abovedisplayshortskip",
            "belowdisplayskip",
            "belowdisplayshortskip",
            "leftskip",
            "rightskip",
            "topskip",
            "splittopskip",
            "tabskip",
            "spaceskip",
            "xspaceskip",
            "parfillskip",

            "skip77",
            #"wombat",
            ]

    s = State()

    mex.put.put(r"\skipdef\wombat=100", s)

    for i, variable in enumerate(VARIABLES):
        s[variable] = mex.value.Glue(space=i)

    for i, variable in enumerate(VARIABLES):
        assert get_glue(rf"\{variable} q",s) == (i, 0.0, 0.0, 0.0, 0)

def test_glue_literal():
    assert get_glue("2spq") == (2.0, 0.0, 0.0, 0, 0)
    assert get_glue("2sp plus 5spq") == (2.0, 5.0, 0.0, 0, 0)
    assert get_glue("2sp minus 5spq") == (2.0, 0.0, 5.0, 0, 0)
    assert get_glue("2sp plus 5sp minus 5spq") == (2.0, 5.0, 5.0, 0, 0)

def test_glue_literal_fil():
    assert get_glue("2sp plus 5fil minus 5fillq") == (2.0, 5.0, 5.0, 1, 2)
    assert get_glue("2sp plus 5filll minus 5fillq") == (2.0, 5.0, 5.0, 3, 2)

def test_glue_repr():
    def _test_repr(s):
        assert str(get_glue(f'{s}q', raw=True)) == s

    _test_repr('2pt plus 5pt')
    _test_repr('2pt plus 5fil')
    _test_repr('2pt plus 5fill')
    _test_repr('2pt plus 5filll minus 5fil')

def test_glue_p69():
    hb = mex.box.HBox()

    boxes = [
            # This is the example on p69 of the TeXbook.

            mex.box.Box(width=5, height=10, depth=0),
            mex.gismo.Leader(space=9.0, stretch=3, shrink=1),
            mex.box.Box(width=6, height=20, depth=0),
            mex.gismo.Leader(space=9.0, stretch=6, shrink=2),
            mex.box.Box(width=3, height=30, depth=0),
            mex.gismo.Leader(space=12.0, stretch=0, shrink=0),
            mex.box.Box(width=8, height=40, depth=0),
            ]

    def glue_widths():
        return [g.width.value for g in boxes
                if isinstance(g, mex.gismo.Leader)]

    hb = mex.box.HBox(boxes)

    assert hb.width == 52
    assert hb.height == 40
    assert glue_widths() == [9.0, 9.0, 12.0]

    hb.fit_to(58)

    assert hb.width == 58
    assert hb.height == 40
    assert glue_widths() == [11.0, 13.0, 12.0]

    hb.fit_to(51)

    assert hb.width == 51
    assert hb.height == 40
    assert [round(x,2) for x in glue_widths()] == [
            8.67, 8.33, 12.0,
            ]

    hb.fit_to(0)

    assert hb.width == 49
    assert hb.height == 40
    assert glue_widths() == [8.0, 7.0, 12.0]

    boxes[1] = mex.gismo.Leader(space=9.0, stretch=3, shrink=1, stretch_infinity=1)
    hb = mex.box.HBox(boxes)

    hb.fit_to(58)

    assert hb.width == 58
    assert hb.height == 40
    assert glue_widths() == [15.0, 9.0, 12.0]

    boxes[3] = mex.gismo.Leader(space=9.0, stretch=6, shrink=2, stretch_infinity=1)
    hb = mex.box.HBox(boxes)

    hb.fit_to(58)

    assert hb.width == 58
    assert hb.height == 40
    assert glue_widths() == [11.0, 13.0, 12.0]

    boxes[3] = mex.gismo.Leader(space=9.0, stretch=6, shrink=2, stretch_infinity=2)
    hb = mex.box.HBox(boxes)

    hb.fit_to(58)

    assert hb.width == 58
    assert hb.height == 40
    assert glue_widths() == [9.0, 15.0, 12.0]

def test_glue_eq():
    a = get_glue('42pt plus 2pt minus 1ptq', raw=True)
    b = get_glue('42pt plus 2pt minus 1ptq', raw=True)
    c = get_glue('42pt plus 2ptq', raw=True)

    for x in [a, b, c]:
        assert isinstance(x, mex.value.Glue)

    assert a==b
    assert a!=c
    assert b!=c
