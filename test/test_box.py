import pytest
import io
from collections import namedtuple
import yex.box
import yex.document
from . import *

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

def test_box_with_text_contents():
    s = yex.document.Document()

    message = 'Hello'

    run_code(
        r"\setbox23=\hbox{" + message + "}",
        doc=s,
        )
    font = s['_font']

    assert ''.join([x.ch for x in s[r'\copy23'].value.contents])==message

    expected_width = float(sum([
            font[c].metrics.width
            for c in message
            ]))

    assert round(
            float(s[r'\copy23'].value.width), 3
            )==round(expected_width, 3)

def test_setbox():
    s = yex.document.Document()
    run_code(
            r"\setbox23=\hbox{}",
            doc=s,
            )
    assert s[r'\box23'].value==yex.box.HBox()

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
        assert isinstance(found[0], yex.gismo.Leader)
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

        assert isinstance(found[0], yex.gismo.Leader)

        assert found[0].width==0, form
        assert found[0].space==0, form

        assert str(found[0].stretch)==expect_stretch, form
        assert str(found[0].shrink)==expect_shrink, form

def test_badness_p97():

    doc = yex.Document()
    badness = doc[r'\badness']

    boxes = [
            yex.box.Box(width=1, height=1, depth=0),
            yex.gismo.Leader(space=10,
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
