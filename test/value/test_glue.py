import io
import pytest
import copy
from yex.document import Document
from yex.value import Number, Dimen, Glue
import yex.exception
from .. import *
import yex.put
import yex.box
import logging

general_logger = logging.getLogger('yex.general')

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
            ]

    s = Document()

    for i, variable in enumerate(VARIABLES):
        s[fr'\{variable}'] = yex.value.Glue(space=Dimen(i))

    for i, variable in enumerate(VARIABLES):
        assert get_glue(fr"\{variable} q",s) == (i, 0.0, 0.0, 0.0, 0)

def test_glue_literal():
    assert get_glue("2ptq") == (2.0, 0.0, 0.0, 0, 0)
    assert get_glue("2pt plus 5ptq") == (2.0, 5.0, 0.0, 0, 0)
    assert get_glue("2pt minus 5ptq") == (2.0, 0.0, 5.0, 0, 0)
    assert get_glue("2pt plus 5pt minus 5ptq") == (2.0, 5.0, 5.0, 0, 0)

def test_glue_literal_fil():
    assert get_glue("2pt plus 5fil minus 5fillq") == (2.0, 5.0, 5.0, 1, 2)
    assert get_glue("2pt plus 5filll minus 5fillq") == (2.0, 5.0, 5.0, 3, 2)

def test_glue_repr():
    def _test_repr(s):
        assert str(get_glue(f'{s}q', raw=True)) == s

    _test_repr('2pt plus 5pt')
    _test_repr('2pt plus 5fil')
    _test_repr('2pt plus 5fill')
    _test_repr('2pt plus 5filll minus 5fil')

def test_glue_p69():
    hb = yex.box.HBox()

    boxes = [
            # This is the example on p69 of the TeXbook.

            yex.box.Box(width=5, height=10, depth=0),
            yex.gismo.Leader(space=9.0, stretch=3, shrink=1),
            yex.box.Box(width=6, height=20, depth=0),
            yex.gismo.Leader(space=9.0, stretch=6, shrink=2),
            yex.box.Box(width=3, height=30, depth=0),
            yex.gismo.Leader(space=12.0, stretch=0, shrink=0),
            yex.box.Box(width=8, height=40, depth=0),
            ]

    def assert_length_in_points(found, expected):
        expected = Dimen(expected, 'pt')

        assert found==expected, f"{found.value}sp == {expected.value}sp"

    def glue_widths():
        return [g.glue.length for g in boxes
                if isinstance(g, yex.gismo.Leader)]

    hb = yex.box.HBox(boxes)

    assert_length_in_points(hb.width, 52)
    assert_length_in_points(hb.height, 40)
    assert glue_widths() == [9.0, 9.0, 12.0]

    hb.fit_to(58)

    assert_length_in_points(hb.width, 58)
    assert_length_in_points(hb.height, 40)
    assert glue_widths() == [11.0, 13.0, 12.0]

    hb.fit_to(51)

    assert_length_in_points(hb.width, 51)
    assert_length_in_points(hb.height, 40)
    assert [round(float(x),2) for x in glue_widths()] == [
            8.67, 8.33, 12.0,
            ]

    hb.fit_to(0)

    assert_length_in_points(hb.width, 49)
    assert_length_in_points(hb.height, 40)
    assert glue_widths() == [8.0, 7.0, 12.0]

    boxes[1] = yex.gismo.Leader(space=9.0, stretch=3, stretch_unit='fil',
            shrink=1)
    hb = yex.box.HBox(boxes)

    hb.fit_to(58)

    assert_length_in_points(hb.width, 58)
    assert_length_in_points(hb.height, 40)
    assert glue_widths() == [15.0, 9.0, 12.0]

    boxes[3] = yex.gismo.Leader(space=9.0, stretch=6, stretch_unit='fil',
            shrink=2)
    hb = yex.box.HBox(boxes)

    hb.fit_to(58)

    assert_length_in_points(hb.width, 58)
    assert_length_in_points(hb.height, 40)
    assert glue_widths() == [11.0, 13.0, 12.0]

    boxes[3] = yex.gismo.Leader(space=9.0, stretch=6, stretch_unit='fill',
            shrink=2)
    hb = yex.box.HBox(boxes)

    hb.fit_to(58)

    assert_length_in_points(hb.width, 58)
    assert_length_in_points(hb.height, 40)
    assert glue_widths() == [9.0, 15.0, 12.0]

def test_leader_construction():
    glue = yex.value.Glue(space=9, stretch=3, shrink=1)

    leader1 = yex.gismo.Leader(space=9, stretch=3, shrink=1)
    leader2 = yex.gismo.Leader(glue=glue)

    assert leader1.space   == leader2.space   == glue.space   == 9
    assert leader1.stretch == leader2.stretch == glue.stretch == 3
    assert leader1.shrink  == leader2.shrink  == glue.shrink  == 1

def test_glue_eq():
    a = get_glue('42pt plus 2pt minus 1ptq', raw=True)
    b = get_glue('42pt plus 2pt minus 1ptq', raw=True)
    c = get_glue('42pt plus 2ptq', raw=True)

    for x in [a, b, c]:
        assert isinstance(x, yex.value.Glue)

    assert a==b
    assert a!=c
    assert b!=c

    assert a!=None
    assert not (a==None)

def test_glue_deepcopy():
    a = [Glue()]
    b = copy.copy(a)

    assert a[0] is b[0]

    c = copy.deepcopy(a)

    assert a[0] is not c[0]

def test_glue_deepcopy():
    # Constructed from literal
    compare_copy_and_deepcopy(Glue(0))

    # Constructed from tokeniser
    compare_copy_and_deepcopy(get_glue("1em plus 2ptq", raw=True))
