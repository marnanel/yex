import mex.box
from collections import namedtuple

DummyCharMetric = namedtuple(
        'DummyCharMetric',
        ['width', 'height', 'depth', 'codepoint'],
        )

def test_box_simple():
    b = mex.box.Box(1, 2, 3)

def test_charbox():
    dcm = DummyCharMetric(
            width=10,
            height=20,
            depth=30,
            codepoint=65,
            )
   
    cb = mex.box.CharBox(dcm)

    assert cb.width == 10
    assert cb.height == 20
    assert cb.depth == 30

def test_hbox():
    hb = mex.box.HBox()

    boxes = [
            mex.box.Box(width=10, height=20, depth=30),
            mex.box.Box(width=40, height=50, depth=60),
            mex.box.Box(width=70, height=80, depth=90),
            ]

    for box in boxes:
        hb.append(box)

    assert hb.width == 120
    assert hb.height == 80
    assert hb.depth == 90

def test_vbox():
    vb = mex.box.VBox()

    boxes = [
            mex.box.Box(width=10, height=20, depth=30),
            mex.box.Box(width=40, height=50, depth=60),
            mex.box.Box(width=70, height=80, depth=90),
            ]

    for box in boxes:
        vb.append(box)

    assert vb.width == 70
    assert vb.height == 330
    assert vb.depth == 0 # XXX check whether this is how it's supposed to work

def test_glue():
    hb = mex.box.HBox()

    boxes = [
            # This is the example on p69 of the TeXbook.

            mex.box.Box(width=5, height=10, depth=0),
            mex.box.Glue(space=9.0, stretch=3, shrink=1),
            mex.box.Box(width=6, height=20, depth=0),
            mex.box.Glue(space=9.0, stretch=6, shrink=2),
            mex.box.Box(width=3, height=30, depth=0),
            mex.box.Glue(space=12.0, stretch=0, shrink=0),
            mex.box.Box(width=8, height=40, depth=0),
            ]

    def glue_lengths():
        return [g.length for g in boxes
                if isinstance(g, mex.box.Glue)]

    hb = mex.box.HBox(boxes)

    assert hb.width == 52
    assert hb.height == 40
    assert glue_lengths() == [9.0, 9.0, 12.0]

    hb.fit_to(58)

    assert hb.width == 58
    assert hb.height == 40
    assert glue_lengths() == [11.0, 13.0, 12.0]

    hb.fit_to(51)

    assert hb.width == 51
    assert hb.height == 40
    assert [round(x,2) for x in glue_lengths()] == [
            8.67, 8.33, 12.0,
            ]

    hb.fit_to(0)

    assert hb.width == 49
    assert hb.height == 40
    assert glue_lengths() == [8.0, 7.0, 12.0]

    boxes[1] = mex.box.Glue(space=9.0, stretch=3, shrink=1, stretch_infinity=1)
    hb = mex.box.HBox(boxes)

    hb.fit_to(58)

    assert hb.width == 58
    assert hb.height == 40
    assert glue_lengths() == [15.0, 9.0, 12.0]

    boxes[3] = mex.box.Glue(space=9.0, stretch=6, shrink=2, stretch_infinity=1)
    hb = mex.box.HBox(boxes)

    hb.fit_to(58)

    assert hb.width == 58
    assert hb.height == 40
    assert glue_lengths() == [11.0, 13.0, 12.0]

    boxes[3] = mex.box.Glue(space=9.0, stretch=6, shrink=2, stretch_infinity=2)
    hb = mex.box.HBox(boxes)

    hb.fit_to(58)

    assert hb.width == 58
    assert hb.height == 40
    assert glue_lengths() == [9.0, 15.0, 12.0]
