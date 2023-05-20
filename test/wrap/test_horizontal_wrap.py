from test import *
import yex
from yex.value import Dimen
import logging

logger = logging.getLogger('yex.general')

ALICE = (
        'Alice was beginning to get very tired of sitting by her sister '
        'on the bank, and of having nothing to do: once or twice she had '
        'peeped into the book her sister was reading, but it had no '
        r'pictures or con\-ver\-sations in it, ``and what is the use of a '
        r'book," thought Alice, ``without pictures or con\-ver\-sation?"'
        )

# When some of the following tests fail, it's useful to check the debug logs.
# The trouble is that lengths in those logs are given in sp, because
# converting would take too long. We can't use sp as a unit, because some
# of them need fractional lengths. But if we use anything else, it will
# be difficult to read the logs.
#
# So we have a function d(), which returns a Dimen where the unit size was
# given by the constant SCALE. Thus if SCALE==1000, d(52) will be a Dimen
# of length 52000sp.

SCALE = 1000

def d(n):
    return yex.value.Dimen(n*SCALE, 'sp')

def badness_from_fit_to(width_pt, boxes, expected_badness):
    width = Dimen(width_pt)
    found = yex.wrap.fitting.Fitting.fit_to(
            size=width,
            line=list(boxes), # take a copy
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

                yex.box.Box(width=d(5), height=d(10), depth=d(0)),
                yex.box.Leader(space=d(9.0), stretch=d(3), shrink=d(1)),
                yex.box.Box(width=d(6), height=d(20), depth=d(0)),
                yex.box.Leader(space=d(9.0), stretch=d(6), shrink=d(2)),
                yex.box.Box(width=d(3), height=d(30), depth=d(0)),
                yex.box.Leader(space=d(12.0), stretch=d(0), shrink=d(0)),
                yex.box.Box(width=d(8), height=d(40), depth=d(0)),

                # yex.wrap requires lines to end with Breakpoints
                yex.box.Breakpoint(),
                ]

        for i, replacement in replace:
            boxes[i] = replacement

        if fit_to_width is not None:
            result = yex.wrap.fitting.Fitting.fit_to(
                    d(fit_to_width), boxes).spaces

            result = [round(x/SCALE, 2) for x in result]

            return result
        else:
            return yex.box.HBox.from_contents(boxes)

    def glue_widths(hb):
        return [g.glue.space.value/SCALE for g in hb
                if isinstance(g, yex.box.Leader)]

    hb = nice_box()

    assert hb.width.value == 52*SCALE
    assert hb.height.value == 40*SCALE
    assert glue_widths(hb) == [9.0, 9.0, 12.0]

    assert nice_box(58) == [11.0, 13.0, 12.0]
    assert nice_box(51) == [8.67, 8.33, 12.0]
    assert nice_box( 0) == [ 8.0,  7.0, 12.0]
    assert nice_box(58,
            replace=[
                (1, yex.box.Leader(space=d(9), stretch=3, stretch_unit='fil',
                    shrink=1)),
                ] )     == [15.0,  9.0, 12.0]

    assert nice_box(58,
            replace=[
                (1, yex.box.Leader(space=d(9), stretch=3, stretch_unit='fil',
                    shrink=1)),
                (3, yex.box.Leader(space=d(9), stretch=6, stretch_unit='fil',
                    shrink=2)),
                ])      == [11.0, 13.0, 12.0]

    assert nice_box(58,
            replace=[
                (1, yex.box.Leader(space=d(9), stretch=3, stretch_unit='fil',
                    shrink=1)),
                (3, yex.box.Leader(space=d(9), stretch=6, stretch_unit='fill',
                    shrink=2)),
                ])      == [9.0, 15.0, 12.0]

def test_decency():

    boxes = [
            yex.box.Box(width=d(1), height=d(1), depth=d(0)),
            yex.box.Leader(space=d(10),
                stretch=d(3),
                shrink=d(3),
                ),
            yex.box.Box(width=d(1), height=d(1), depth=d(0)),
            yex.box.Breakpoint(),
            ]

    for width, expected_decency in [
            ( 9,  yex.wrap.TIGHT),
            (13,  yex.wrap.DECENT),
            (14,  yex.wrap.LOOSE),
            (15,  yex.wrap.VERY_LOOSE),
            ]:

        found = yex.wrap.fitting.Fitting.fit_to(
                size=d(width),
                line=boxes,
                )

        assert found.decency == expected_decency

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

def wrap_alice(width):
    doc = yex.Document()
    doc[r'\hsize'] = yex.value.Dimen(width)
    doc[r'\pretolerance'] = 2000

    run_code(
            setup=r'\def\-{\discretionary{-}{}{}}',
            call=ALICE,
            mode='vertical',
            output='dummy',
            doc=doc,
            )

    wrapped = doc['_output'].hboxes()

    def munge(item):
        if isinstance(item, yex.box.Leader):
            return ' '
        else:
            try:
                return item.ch
            except:
                return ''

    found = []
    for line in wrapped:
        assert isinstance(line, yex.box.HBox)
        as_text = ''.join([munge(item) for item in line.contents])
        if as_text:
            found.append(as_text.strip())

    result = '\n'.join(found)
    logger.debug("the result of wrapping is:\n\n%s\n\n", result)
    return result

def test_wrap_alice():

    # First lines are short because of the paragraph indent

    assert wrap_alice(160) == """
Alice was beginning to get very
tired of sitting by her sister on the
bank, and of having nothing to do:
once or twice she had peeped into the
book her sister was reading, but it
had no pictures or conversations in
it, ``and what is the use of a book,"
thought Alice, ``without pictures or
conversation?"
    """.strip()

    assert wrap_alice(200) == """
Alice was beginning to get very tired of
sitting by her sister on the bank, and of having
nothing to do: once or twice she had peeped
into the book her sister was reading, but it had
no pictures or conversations in it, ``and what
is the use of a book," thought Alice, ``without
pictures or conversation?"
    """.strip()

def test_wrap_wordbox_source_index():
    doc = yex.Document()
    doc[r'\hsize'] = yex.value.Dimen(150)
    doc[r'\pretolerance'] = 2000

    wrapped = run_code(
            (
                "This is the song that never ends. It just goes on and on, "
                "my friends."
                ),
            find='hboxes',
            output='dummy',
            doc=doc,
            )

    assert len(wrapped)==3

    wordboxes = [wbox for hbox in wrapped
            for wbox in hbox
            if isinstance(wbox, yex.box.WordBox)]

    wordbox_indexes = [w.source_index for w in wordboxes]
    assert len(wordbox_indexes)==15
    assert len(set(wordbox_indexes))==15, 'wordbox_indexes are unique'
    assert sorted(wordbox_indexes)==wordbox_indexes, \
            'wordbox_indexes are ordered'

if __name__=='__main__':
    for i in range(100, 200, 10):
        try:
            print(i, wrap_alice(i))
        except ValueError:
            print(i, '-- no')
