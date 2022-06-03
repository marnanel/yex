from test import *
import yex
import yex.box
import yex.wrap
from yex.value import Dimen

ALICE = (
        'Alice was beginning to get very tired of sitting by her sister '
        'on the bank, and of having nothing to do: once or twice she had '
        'peeped into the book her sister was reading, but it had no '
        r'pictures or con\-ver\-sations in it, ``and what is the use of a '
        r'book," thought Alice, ``without pictures or con\-ver\-sation?"'
        )

def badness_from_fit_to(width_pt, boxes, expected_badness):
    width = Dimen(width_pt)
    found = yex.wrap.fit_to(
            size=width,
            line=boxes,
            )

    assert found.badness == expected_badness, f"{width_pt}pt"

def test_badness_p97():

    doc = yex.Document()

    boxes = [
            yex.box.Box(width=1, height=1, depth=0),
            yex.box.Leader(space=10,
                stretch=0,
                shrink=10,
                ),
            yex.box.Box(width=1, height=1, depth=0),
            yex.box.Breakpoint(),
            ]

    badness_from_fit_to(12, boxes, 0)

    badness_from_fit_to(3, boxes, 73)

    # all overfull boxes have a badness of one million
    badness_from_fit_to(0, boxes, 1000000)

def test_glue_p69():

    def nice_box(
            fit_to_width=None,
            replace=[],
            ):
        boxes = [
                # This is the example on p69 of the TeXbook.

                yex.box.Box(width=5, height=10, depth=0),
                yex.box.Leader(space=9.0, stretch=3, shrink=1),
                yex.box.Box(width=6, height=20, depth=0),
                yex.box.Leader(space=9.0, stretch=6, shrink=2),
                yex.box.Box(width=3, height=30, depth=0),
                yex.box.Leader(space=12.0, stretch=0, shrink=0),
                yex.box.Box(width=8, height=40, depth=0),

                # yex.wrap requires lines to end with Breakpoints
                yex.box.Breakpoint(),
                ]

        for i, replacement in replace:
            boxes[i] = replacement

        if fit_to_width is not None:
            result = yex.wrap.fit_to(
                    yex.value.Dimen(fit_to_width),
                    boxes).spaces

            result = [round(float(x),2) for x in result]

            return result
        else:
            return yex.box.HBox(boxes)

    def assert_length_in_points(found, expected):
        expected = Dimen(expected, 'pt')

        assert found==expected, f"{found.value}sp == {expected.value}sp"

    def glue_widths(hb):
        return [float(g.glue.space) for g in hb
                if isinstance(g, yex.box.Leader)]

    hb = nice_box()

    assert_length_in_points(hb.width, 52)
    assert_length_in_points(hb.height, 40)
    assert glue_widths(hb) == [9.0, 9.0, 12.0]

    assert nice_box(58) == [11.0, 13.0, 12.0]
    assert nice_box(51) == [8.67, 8.33, 12.0]
    assert nice_box( 0) == [ 8.0,  7.0, 12.0]
    assert nice_box(58,
            replace=[
                (1, yex.box.Leader(space=9.0, stretch=3, stretch_unit='fil',
                    shrink=1)),
                ] )     == [15.0,  9.0, 12.0]

    assert nice_box(58,
            replace=[
                (1, yex.box.Leader(space=9.0, stretch=3, stretch_unit='fil',
                    shrink=1)),
                (3, yex.box.Leader(space=9.0, stretch=6, stretch_unit='fil',
                    shrink=2)),
                ])      == [11.0, 13.0, 12.0]

    assert nice_box(58,
            replace=[
                (1, yex.box.Leader(space=9.0, stretch=3, stretch_unit='fil',
                    shrink=1)),
                (3, yex.box.Leader(space=9.0, stretch=6, stretch_unit='fill',
                    shrink=2)),
                ])      == [9.0, 15.0, 12.0]

def test_decency():

    boxes = [
            yex.box.Box(width=1, height=1, depth=0),
            yex.box.Leader(space=10,
                stretch=3,
                shrink=3,
                ),
            yex.box.Box(width=1, height=1, depth=0),
            yex.box.Breakpoint(),
            ]

    for width_in_pt, expected_decency in [
            ( 9,  yex.wrap.TIGHT),
            (13,  yex.wrap.DECENT),
            (14,  yex.wrap.LOOSE),
            (15,  yex.wrap.VERY_LOOSE),
            ]:

        found = yex.wrap.fit_to(
                size=Dimen(width_in_pt),
                line=boxes,
                )

        assert found.decency == expected_decency, f"{width_in_pt}pt"

def test_badness_with_no_glue():

    boxes = [
            yex.box.Box(width=10, height=1, depth=0),
            yex.box.Breakpoint(),
        ]

    # exact fit
    badness_from_fit_to(10, boxes, 0)

    # overfull
    badness_from_fit_to(1, boxes, 1000000)

    # underfull
    badness_from_fit_to(100, boxes, 10000)

def test_wrap_alice():

    def wrap_alice(width):
        doc = yex.Document()
        doc[r'\hsize'] = yex.value.Dimen(width)
        doc[r'\pretolerance'] = 2000

        run_code(
                setup=r'\def\-{\discretionary{-}{}{}}',
                call=ALICE,
                doc=doc)
        doc.end_all_groups()

        wrapped = doc.output[0]

        assert isinstance(wrapped, yex.box.VBox)

        def munge(item):
            if isinstance(item, yex.box.Leader):
                return ' '
            else:
                try:
                    return item.ch
                except:
                    return ''

        found = []
        for line in wrapped.contents:
            assert isinstance(line, yex.box.HBox)
            as_text = ''.join([munge(item) for item in line.contents])
            if as_text:
                found.append(as_text.strip())

        return found

    assert wrap_alice(180) == [
            'Alice was beginning to get very tired of',
            'sitting by her sister on the bank, and of',
            'having nothing to do: once or twice she',
            'had peeped into the book her sister was',
            'reading, but it had no pictures or conver',
            r'sations in it, \and what is the use of a',
            r'book," thought Alice, \without pictures',
            'or conversation?"',
            ]

    assert wrap_alice(200) == [
            'Alice was beginning to get very tired of',
            'sitting by her sister on the bank, and of',
            'having nothing to do: once or twice she had',
            'peeped into the book her sister was reading,',
            'but it had no pictures or conversations in',
            'it, \\and what is the use of a book," thought',
            'Alice, \\without pictures or conversation?"',
            ]
