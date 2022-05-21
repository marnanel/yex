import pytest
import io
from collections import namedtuple
import yex.box
import yex.document
import re
import logging
from . import *

logger = logging.getLogger('yex.general')

DummyCharMetric = namedtuple(
        'DummyCharMetric',
        ['width', 'height', 'depth', 'codepoint'],
        )

ALICE = (
        "Alice was beginning to get very tired of sitting by her sister "
        "on the bank, and of having nothing to do: once or twice she had "
        "peeped into the book her sister was reading, but it had no "
        "pictures or conversations in it, ``and what is the use of a "
        "book,\" thought Alice, ``without pictures or conversation?"
        )

def test_box_simple():
    b = yex.box.Box(1, 2, 3)

def test_charbox():

    s = yex.document.Document()

    cb = yex.box.CharBox(
            font = s['_font'],
            ch = 'x',
            )

    assert int(cb.width) == 5
    assert int(cb.height) == 4
    assert int(cb.depth) == 0
    assert cb.ch == 'x'

def test_hbox():
    hb = yex.box.HBox()

    boxes = [
            yex.box.Box(width=10, height=20, depth=30),
            yex.box.Box(width=40, height=50, depth=60),
            yex.box.Box(width=70, height=80, depth=90),
            ]

    for box in boxes:
        hb.append(box)

    assert hb.width == 120
    assert hb.height == 80
    assert hb.depth == 90

def test_vbox():
    vb = yex.box.VBox()

    boxes = [
            yex.box.Box(width=10, height=20, depth=30),
            yex.box.Box(width=40, height=50, depth=60),
            yex.box.Box(width=70, height=80, depth=90),
            ]

    for box in boxes:
        vb.append(box)

    assert vb.width == 70
    assert vb.height == 20+30+50+60+80
    assert vb.depth == 90

def test_box_registers():
    """
    If you look up boxNN directly, it destroys the box.
    If you use the alias "copyNN", it doesn't.
    """

    s = yex.document.Document()
    s[r'\box23'] = yex.box.Box(width=20.0)
    assert s[r'\box23'].value.width == 20.0
    assert s[r'\box23'].value.width == 0.0

    s[r'\box23'] = yex.box.Box(width=20.0)
    assert s[r'\copy23'].value.width == 20.0
    assert s[r'\copy23'].value.width == 20.0
    assert s[r'\box23'].value.width == 20.0
    assert s[r'\box23'].value.width == 0.0
    assert s[r'\copy23'].value.width == 0.0

    s[r'\copy23'] = yex.box.Box(width=20.0)
    assert s[r'\copy23'].value.width == 20.0
    assert s[r'\box23'].value.width == 20.0
    assert s[r'\box23'].value.width == 0.0

def get_hbox(doc, message):
    run_code(
        r"\setbox23=\hbox{" + message + "}",
        doc=doc,
        )

    return doc[r'\copy23'].value

def test_box_with_text_contents():
    doc = yex.Document()

    message = 'Hello'

    hbox = get_hbox(
            doc = doc,
            message = message,
            )

    font = doc['_font']

    assert ''.join([x.ch for x in hbox.contents])==message

    expected_width = float(sum([
            font[c].metrics.width
            for c in message
            ]))

    assert round(float(hbox.width), 3)==round(expected_width, 3)

def test_setbox():
    doc = yex.Document()

    hbox = get_hbox(doc=doc, message="")
    assert hbox==yex.box.HBox()

def assert_munged_for_breakpoints(hbox, expected, message):
    def munge(thing):
        if isinstance(thing, yex.box.Leader):
            return ' '
        elif isinstance(thing, (yex.box.WordBox, yex.box.CharBox)):
            return thing.ch
        elif isinstance(thing, yex.box.Breakpoint):
            return f'^{thing.penalty}'
        elif isinstance(thing, yex.box.MathSwitch):
            return '$'
        else:
            return thing.__class__.__name__[0]

    def munged_list(things):
        return ''.join([munge(x) for x in things])

    assert munged_list(hbox.with_breakpoints.contents)==\
            expected, message
    assert munged_list(hbox.contents)==\
            re.sub(r'\^[0-9]+', '', expected), message

def test_hbox_adding_breakpoints_via_tokeniser():
    # This is an integration test, so it can't test absolutely everything

    def run(message, expected):
        doc = yex.Document()

        hbox = get_hbox(
                message=message, doc=doc)

        assert_munged_for_breakpoints(hbox, expected, message)

    run("Hello world", "^0Hello^0 world^0")
    run("Can't complain", "^0Can't^0 complain^0")
    # the ligature doesn't confuse it
    run("Off you go", "^0O(0b)^0 you^0 go^0")

def test_hbox_adding_breakpoints_directly():

    def run(things, expected):
        hbox = yex.box.HBox()

        for thing in things:
            hbox.append(thing)

        assert_munged_for_breakpoints(hbox, expected, things)

        hbox = yex.box.HBox()
        hbox.extend(things)

        assert_munged_for_breakpoints(hbox, expected, things)

    nullfont = yex.font.Default()
    wordbox = yex.box.WordBox(nullfont)
    for c in 'spong':
        wordbox.append(c)
    kern = yex.box.Kern(width=1.0)

    glue = yex.box.Leader(space=10.0, stretch=0.0, shrink=0.0)

    math_on = yex.box.MathSwitch(True)
    math_off = yex.box.MathSwitch(False)
    discretionary = yex.box.DiscretionaryBreak(0,0,0)
    penalty = yex.box.Penalty(20)

    whatsit = yex.box.Whatsit(None)

    run([wordbox], '^0spong^0')
    run([glue], '^0 ^0')
    run([wordbox, glue], '^0spong^0 ^0')
    run([glue, wordbox], '^0 spong^0')
    run([wordbox, glue, glue, wordbox], '^0spong^0  spong^0')
    run([wordbox, wordbox], '^0spongspong^0')

    run([wordbox, kern, wordbox], '^0spongKspong^0')
    run([wordbox, kern, glue, wordbox], '^0spong^0K spong^0')

    run([wordbox, math_on, wordbox], '^0spong$spong^0')
    run([wordbox, math_off, wordbox], '^0spong$spong^0')

    run([wordbox, math_on, glue, wordbox], '^0spong$ spong^0')
    run([wordbox, math_off, glue, wordbox], '^0spong^0$ spong^0')

    run([wordbox, penalty, wordbox], '^0spong^20Pspong^0')
    run([wordbox, penalty, glue, wordbox], '^0spong^20P spong^0')

    run([wordbox, discretionary, wordbox], '^0spong^50Dspong^0')
    run([wordbox, discretionary, glue, wordbox], '^0spong^50D^0 spong^0')

    # XXX The penalty for discretionary hyphens is changed using
    # \hyphenpenalty and \exhyphenpenalty. Currently these have to
    # be specified to HBox.append() as optional parameters, which
    # is pretty daft. Boxes should know what document they're from.
    # When they do, we should test that here too. See issue #50.

    # whatsits add no extra breakpoints
    run([wordbox, whatsit, wordbox], '^0spongWspong^0')
    run([wordbox, whatsit, glue, wordbox], '^0spongW^0 spong^0')

def test_box_init_from_tokeniser():

    with io.StringIO("hello") as f:
        s = yex.document.Document()
        t = yex.parse.Tokeniser(s, f)

        with pytest.raises(yex.exception.YexError):
            box = yex.box.Box(t)

        with pytest.raises(yex.exception.YexError):
            hbox = yex.box.HBox(t)

def test_tex_logo_p66(capsys, ):
    string = (
        r"\setbox0=\hbox{T\kern-.1667em\lower.5ex\hbox{E}\kern-.125emX}"
        r"\showbox0"
        )
    expected = (
            # The TeXbook gives the font as "tenrm", but that's an alias
            # given in plain.tex, which isn't loaded here.
            r'\hbox(6.83331+2.15277)x18.6108' '\n'
            r'.\cmr10 T' '\n'
            r'.\kern -1.66702' '\n'
            r'.\hbox(6.83331+0.0)x6.80557, shifted 2.15277' '\n'
            r'..\cmr10 E' '\n'
            r'.\kern -1.25' '\n'
            r'.\cmr10 X' '\n'
            )

    assert run_code(
            string,
            find='chars',
            )==''

    found = capsys.readouterr().out

    print('-- Found')
    print(found)
    print('-- Expected')
    print(expected)

    compare_strings_with_reals(
            found,
            expected,
            tolerance=0.01,
            )

def test_wordbox_append_illegal_args():
    font = yex.font.get_font_from_name(None)
    wb = yex.box.WordBox(font=font)

    with pytest.raises(TypeError):
        wb.append(123)

    with pytest.raises(TypeError):
        wb.append(None)

    with pytest.raises(TypeError):
        wb.append('Hello world')

    with pytest.raises(TypeError):
        wb.append('')

def test_wordbox_width():
    font = yex.font.get_font_from_name(None)

    def total_lengths_of_chars(s):
        widths = max_height = max_depth = 0
        for c in s:
            metrics = font[c].metrics
            widths += metrics.width
            max_height = max(metrics.height, max_height)
            max_depth = max(metrics.depth, max_depth)
        return widths, max_height, max_depth

    # "expected" is the expected difference between the width of the word
    # and the total of the widths of all its characters.
    # The differences are caused by kerns and ligatures.
    for word, expected in [
            ('X',           0),
            ('XX',          0),
            ('I',           0),
            ('II',     -0.278), # there is a kern
            ('o',           0),
            ('of',          0),
            ('off',    -3.056), # "ff" ligature
            ('offi',   -5.834), # "ffi" ligature
            ('offic',  -5.834),
            ('office', -5.834),
            ]:
        wb = yex.box.WordBox(font=font)
        assert wb.width==0

        for c in word:
            wb.append(c)

        w, h, d = total_lengths_of_chars(word)

        # Height and depth aren't affected by kerns and ligatures
        assert wb.height == h, word
        assert wb.depth == d, word

        # But width is!
        difference = wb.width - w
        assert difference == yex.value.Dimen(expected), word

def test_box_indexing():
    hb = yex.box.HBox()

    boxes = [
            yex.box.Box(width=10, height=20, depth=30),
            yex.box.Box(width=40, height=50, depth=60),
            yex.box.Box(width=70, height=80, depth=90),
            ]

    for box in boxes:
        hb.append(box)

    assert hb[0]==boxes[0]
    assert hb[1]==boxes[1]
    assert hb[2]==boxes[2]

    assert hb[-1]==boxes[2]
    assert hb[-2]==boxes[1]
    assert hb[-3]==boxes[0]

    assert len(hb)==3
    assert hb[0]==boxes[0]

def test_box_slicing():
    hb = yex.box.HBox()

    for width in [1, 2, 3, 4, 5]:
        hb.append(yex.box.Box(width=width, height=1, depth=1))

    def describe(box):
        return '-'.join([str(int(x.width)) for x in box.contents])

    assert describe(hb)=='1-2-3-4-5'
    assert describe(hb[1:])=='2-3-4-5'
    assert describe(hb[3:])=='4-5'
    assert describe(hb[:3])=='1-2-3'
    assert describe(hb[:1])=='1'
    assert describe(hb[-2:])=='4-5'
    assert describe(hb[-3:-1])=='3-4'
    assert describe(hb[1:-1:2])=='2-4'

def test_hrule_dimensions():

    for cmd, expect_w, expect_h, expect_d in [

            (r"\hrule width5pt",                    5.0, 0.4, 0.0),
            (r"\hrule",                             'inherit', 0.4, 0.0),
            (r"\hrule width5pt height5pt",          5.0, 5.0, 0.0),
            (r"\hrule width5pt height5pt depth2pt", 5.0, 5.0, 2.0),
            (r"\hrule width5pt height5pt width2pt", 2.0, 5.0, 0.0),

            (r"\vrule width5pt",                    5.0, 'inherit', 'inherit'),
            (r"\vrule",                             0.4, 'inherit', 'inherit'),
            (r"\vrule width5pt height5pt",          5.0, 5.0, 'inherit'),
            (r"\vrule width5pt height5pt depth2pt", 5.0, 5.0, 2.0),
            (r"\vrule width5pt height5pt width2pt", 2.0, 5.0, 'inherit'),

            ]:

        results = run_code(
                f"{cmd} q",
                )
        found = [t for t in results['saw']
                if not isinstance(t, yex.parse.Space)]

        def to_pt(v):
            if v=='inherit':
                return v

            return yex.value.Dimen(v, 'pt')

        assert len(found)==2
        assert isinstance(found[0], yex.box.Rule)
        assert found[0].width  == to_pt(expect_w), f"{cmd} w"
        assert found[0].height == to_pt(expect_h), f"{cmd} h"
        assert found[0].depth  == to_pt(expect_d), f"{cmd} d"
        assert found[1].ch=='q'

def test_hskip_vskip():

    for form in ['hskip', 'vskip']:
        found = run_code(
                fr"\{form} 1.0pt plus 2.0pt minus 0.5pt",
                find='saw')

        assert len(found)==1
        assert isinstance(found[0], yex.box.Leader)
        assert found[0].width==yex.value.Dimen(1.0, 'pt')
        assert found[0].space==yex.value.Dimen(1.0, 'pt')
        assert found[0].stretch==yex.value.Dimen(2.0, 'pt')
        assert found[0].shrink==yex.value.Dimen(0.5, 'pt')

def test_hfill_etc():

    for form, expect_stretch, expect_shrink in [

            (r'\hfil',     '1fil',   '0pt'),
            (r'\hfill',    '1fill',  '0pt'),
            (r'\hfilll',   '1filll', '0pt'),
            (r'\hss',      '1fil',   '1fil'),
            (r'\hfilneg',  '-1fil',  '0pt'),

            (r'\vfil',     '1fil',   '0pt'),
            (r'\vfill',    '1fill',  '0pt'),
            # there is no \vfilll
            (r'\vss',      '1fil',   '1fil'),
            (r'\vfilneg',  '-1fil',  '0pt'),

            ]:

        found = run_code(form,
                find='saw')

        assert isinstance(found[0], yex.box.Leader)

        assert found[0].width==0, form
        assert found[0].space==0, form

        assert str(found[0].stretch)==expect_stretch, form
        assert str(found[0].shrink)==expect_shrink, form

def test_badness_p97():

    doc = yex.Document()
    badness = doc[r'\badness'] # save a ref for the "badness_param" argument

    boxes = [
            yex.box.Box(width=1, height=1, depth=0),
            yex.box.Leader(space=10,
                stretch=0,
                shrink=10,
                ),
            yex.box.Box(width=1, height=1, depth=0),
            ]

    hb = yex.box.HBox(boxes)
    assert hb.badness == 0
    assert int(doc[r'\badness'])==0

    hb.fit_to(3, badness_param = badness)
    assert hb.badness == 73
    assert int(doc[r'\badness'])==73

    # all overfull boxes have a badness of one million
    hb.fit_to(0, badness_param = badness)
    assert hb.badness == 1000000
    assert int(doc[r'\badness'])==1000000

def test_decency():

    hb = yex.box.HBox([
            yex.box.Box(width=1, height=1, depth=0),
            yex.box.Leader(space=10,
                stretch=3,
                shrink=3,
                ),
            yex.box.Box(width=1, height=1, depth=0),
            ])

    for width_in_pt, expected in [
            ( 9,  hb.TIGHT),
            (13,  hb.DECENT),
            (14,  hb.LOOSE),
            (15,  hb.VERY_LOOSE),
            ]:
        hb.fit_to(width_in_pt)

        assert hb.decency == expected, f"{width_in_pt}pt"

def test_badness_of_slices():

    doc = yex.Document()
    badness = doc[r'\badness'] # save a ref for the "badness_param" argument

    hb = yex.box.HBox([
        yex.box.Box(width=1, height=1, depth=0),
        yex.box.Leader(space=10,
            stretch=0,
            shrink=10,
            ),
        yex.box.Box(width=1, height=1, depth=0),
        yex.box.Leader(space=10,
            stretch=0,
            shrink=10,
            ),
        yex.box.Box(width=1, height=1, depth=0),
        ])

    for name, bit, badness_at_3pt in [
            ('whole thing', hb, 100),
            ('first bit', hb[:3], 73),
            ('last bit', hb[-3:], 73),
            ]:

        assert bit.badness == 0, name

        for fitting, expected in [
                (3, badness_at_3pt),
                (0, 1000000),
                ]:

            logger.debug(
                    "fitting %s (the %s) to %spt; expecting badness of %s",
                    bit, name, fitting, expected)

            bit.fit_to(fitting, badness_param = badness)
            assert bit.badness == expected, name
            assert int(doc[r'\badness'])==expected, name

def test_badness_with_no_glue():

    hbox = yex.box.HBox([
        yex.box.Box(width=10, height=1, depth=0),
        ])

    # exact fit
    hbox.fit_to(10)
    assert hbox.badness == 0

    # overfull
    hbox.fit_to(1)
    assert hbox.badness == 1000000

    # underfull
    hbox.fit_to(100)
    assert hbox.badness == 10000

def test_vbox_depth_is_dimen():
    v = yex.box.VBox()
    assert isinstance(v.depth, yex.value.Dimen)

def test_size_of_empty_box():

    for box in [
            yex.box.VBox(),
            yex.box.HBox(),
            ]:
        assert float(box.height)==0, box
        assert float(box.width)==0, box
        assert float(box.depth)==0, box

def test_wordbox_ligature_creation():

    # Also tests whether WordBoxes are created correctly.

    doc = yex.Document()

    run_code(r'\chardef\eff=102', doc=doc)

    for string, expected in [

            # all letters, but one ligature ("ff")
            # which becomes \x0b in the font cmr10
            (r'off',         'o\x0b'),

            # two non-letter characters and some letters;
            # "``" becomes an open quote, which is '\' in cmr10
            (r'``ABC',       '\\ABC'),

            # "off" again, except that the middle "f" is specified
            # using \char, which should make no difference
            (r'o\char102 f', 'o\x0b'),

            # "off" again, except that the middle "f" is specified
            # using \chardef
            (r'o\eff f', 'o\x0b'),

            # Also, let's test the em dash.
            (r'a---b', 'a|b'),
            ]:
        received = run_code(
                string,
                doc=doc,
                find='list')
        doc.end_all_groups()

        found = ''.join([x.split(' ')[1] for x in received.showbox()
                # not using r'' because of a bug in vi's syntax highlighting
                if x.startswith('..\\') and
                not x.startswith(r'..\glue')])

        assert expected==found, received.showbox()

def test_wordbox_remembers_ligature():
    doc = yex.Document()
    received = run_code(r'a---b``c', doc=doc, find='list')
    doc.end_all_groups()

    found = [x.split(' ', maxsplit=1)[1] for x in received.showbox()
            if 'cmr10' in x]

    assert found==['a', '| (ligature ---)', 'b', r'\ (ligature ``)', 'c']
