import mex.box
from collections import namedtuple

DummyCharMetric = namedtuple(
        'DummyCharMetric',
        ['width', 'height', 'depth'],
        )

def test_box_simple():
    b = mex.box.Box(1, 2, 3)

def test_charbox():
    dcm = DummyCharMetric(
            width=10,
            height=20,
            depth=30,
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


