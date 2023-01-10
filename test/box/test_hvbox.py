import pytest
import io
from collections import namedtuple
import yex
import re
import logging
from test import *

logger = logging.getLogger('yex.general')

DummyCharMetric = namedtuple(
        'DummyCharMetric',
        ['width', 'height', 'depth', 'codepoint'],
        )

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

def box_getstate(code, setup, expected):

    doc = yex.Document()

    run_code(
            code,
            setup = setup,
            mode = 'vertical',
            doc = doc,
            )
    doc.save()

    box = doc.contents[0]

    found = box.__getstate__()

    assert found==expected

def test_hbox_getstate(yex_test_fs):
    # Using yex_test_fs to pull in the italic font
    PHRASE = (r'In the end it took me a dictionary / '
            r'to find out the meaning of '
            r'{\ital unrequited}.')

    SETUP = r'\font\ital=cmti10'

    EXPECTED_SPACE = [218453, 109226, 0, 72818, 0]
    EXPECTED = {
            'page': [{
            'font': 'tenrm',
            'hbox': [
                {r'breakpoint': []},
                'In',
                {r'breakpoint': []},
                EXPECTED_SPACE,
                'the',
                {r'breakpoint': []},
                EXPECTED_SPACE,
                'end',
                {r'breakpoint': []},
                EXPECTED_SPACE,
                'it',
                {r'breakpoint': []},
                EXPECTED_SPACE,
                'to',                   # "to"[ok]
                {'kern': 18205},
                'ok',                   # [to]"ok"
                {r'breakpoint': []},
                EXPECTED_SPACE,
                'me',
                {r'breakpoint': []},
                EXPECTED_SPACE,
                'a',
                {r'breakpoint': []},
                EXPECTED_SPACE,
                'dictionary',
                {r'breakpoint': []},
                EXPECTED_SPACE,
                '/',
                {r'breakpoint': []},
                EXPECTED_SPACE,
                'to',
                {r'breakpoint': []},
                EXPECTED_SPACE,
                '\x0cnd',               # "find" with ligature
                {r'breakpoint': []},
                EXPECTED_SPACE,
                'out',
                {r'breakpoint': []},
                EXPECTED_SPACE,
                'the',
                {r'breakpoint': []},
                EXPECTED_SPACE,
                'meaning',
                {r'breakpoint': []},
                EXPECTED_SPACE,
                'of',
                {r'breakpoint': []},
                EXPECTED_SPACE,

                {'font': 'cmti10'},
                'unr',
                {'kern': -33497},
                'e',
                {'kern': -33497},
                'quite',
                {'kern': -33497},
                'd',
                {'font': 'tenrm'},

                '.',
                ],
                }],
    }

    box_getstate(
            code = r'\shipout\hbox{' + PHRASE + '}',
            setup = SETUP,
            expected = EXPECTED,
            )

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

def test_vbox_getstate():
    TEXT = r'''I told you before about a dinner I had one evening
    with my friend Mr Leakey, a magician who lives in London.
    Before I left him I promised to spend a day with him some time,
    and now I am going to tell you about that day.

    '''
    # TODO the gap at the end is to force a para break;
    # there's currently a bug in Vertical where it doesn't
    # add one at the end automatically.

    EXPECTED = {
            "page": [
                {
                    "vbox": [
                        {
                            "font": "tenrm",
                            "hbox": [
                                {
                                    "hbox": []
                                    },
                                "I",
                                [
                                    218453,
                                    109226,
                                    0,
                                    72818,
                                    0
                                    ],
                                "told",
                                [
                                    218453,
                                    109226,
                                    0,
                                    72818,
                                    0
                                    ],
                                "y",
                                {
                                    "kern": -18205
                                    },
                                "ou",
                                [
                                    218453,
                                    109226,
                                    0,
                                    72818,
                                    0
                                    ],
                                "b",
                                {
                                    "kern": 18205
                                    },
                                "efore",
                                [
                                    218453,
                                    109226,
                                    0,
                                    72818,
                                    0
                                    ],
                                "ab",
                                {
                                    "kern": 18205
                                    },
                                "out",
                                [
                                    218453,
                                    109226,
                                    0,
                                    72818,
                                    0
                                    ],
                        "a",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "dinner",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "I",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "had",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "one",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "ev",
                        {
                                "kern": -18205
                                },
                        "ening",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "with",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "m",
                        {
                                "kern": -18205
                                },
                        "y",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "friend",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "Mr",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "Leak",
                        {
                                "kern": -18205
                                },
                        "ey",
                        {
                                "kern": -54614
                                },
                        ",",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "a",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "magician",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "who",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "liv",
                        {
                                "kern": -18205
                                },
                        "es",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "in",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "London.",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "Before",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "I",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "left",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "him",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "I",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "promised",
                        0
                    ]
                },
                {
                        "font": "tenrm",
                        "hbox": [
                            "to",
                            [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                            "sp",
                            {
                                "kern": 18205
                                },
                            "end",
                            [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                            "a",
                            [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                            "da",
                            {
                                "kern": -18205
                                },
                            "y",
                            [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                            "with",
                            [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                            "him",
                            [
                                    218453,
                                    109226,
                                    0,
                                    72818,
                                    0
                                    ],
                        "some",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "time,",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "and",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "no",
                        {
                                "kern": -18205
                                },
                        "w",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "I",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "am",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "going",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "to",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "tell",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "y",
                        {
                                "kern": -18205
                                },
                        "ou",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "ab",
                        {
                                "kern": 18205
                                },
                        "out",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "that",
                        [
                                218453,
                                109226,
                                0,
                                72818,
                                0
                                ],
                        "da",
                        {
                                "kern": -18205
                                },
                        "y",
                        {
                                "kern": -54614
                                },
                        ".",
                        {
                                "penalty": 10000
                                },
                        {
                                "ch": "",
                                "leader": [
                                    0,
                                    65536,
                                    1
                                    ]
                                },
                            0
                        ]
                    }
                ]
            }
        ]
    }

    box_getstate(
            code = TEXT,
            setup = r'\hsize=595pt\parindent=0pt',
            expected = EXPECTED,
            )

def test_box_registers():
    """
    If you look up boxNN directly, it destroys the box.
    If you use the alias "copyNN", it doesn't.
    """

    s = yex.document.Document()
    s[r'\box23'] = yex.box.Box(width=20.0)
    assert s[r'\box23'].width == 20.0
    assert s[r'\box23'].width == 0.0

    s[r'\box23'] = yex.box.Box(width=20.0)
    assert s[r'\copy23'].width == 20.0
    assert s[r'\copy23'].width == 20.0
    assert s[r'\box23'].width == 20.0
    assert s[r'\box23'].width == 0.0
    assert s[r'\copy23'].width == 0.0

    s[r'\copy23'] = yex.box.Box(width=20.0)
    assert s[r'\copy23'].width == 20.0
    assert s[r'\box23'].width == 20.0
    assert s[r'\box23'].width == 0.0

def get_hbox(doc, message):
    run_code(
        r"\setbox23=\hbox{" + message + "}",
        doc=doc,
        )

    return doc[r'\copy23']

def test_box_with_text_contents():
    doc = yex.Document()

    message = 'Hello'

    hbox = get_hbox(
            doc = doc,
            message = message,
            )

    assert box_contents_to_string(hbox)=='^ '+message

    font = doc['_font']

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

    assert ''.join([munge(x) for x in hbox])==expected, message

def test_hbox_adding_breakpoints_via_tokeniser():
    # This is an integration test, so it can't test absolutely everything

    def run(message, expected):
        doc = yex.Document()

        hbox = get_hbox(
                message=message, doc=doc)

        assert_munged_for_breakpoints(hbox, expected, message)

    run("Hello world", "^0Hello^0 world")
    run("Can't complain", "^0Can't^0 complain")
    # the ligature doesn't confuse it
    run("Off you go", "^0Off^0 you^0 go")

def test_hbox_adding_breakpoints_directly():

    doc = yex.Document()

    def run(things, expected):
        e = doc.open(r"")
        doc['_mode'] = 'horizontal'
        mode = doc['_mode']

        for thing in things:
            mode.handle(
                    item=thing,
                    tokens=e,
                    )

        assert_munged_for_breakpoints(mode.list, expected, str(things))

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

    whatsit = yex.box.Whatsit(
            on_box_render = lambda: None,
            )

    run([wordbox], '^0spong')
    run([glue], '^0 ')
    run([wordbox, glue], '^0spong^0 ')
    run([glue, wordbox], '^0 spong')
    run([wordbox, glue, glue, wordbox], '^0spong^0  spong')
    run([wordbox, wordbox], '^0spongspong')

    run([wordbox, kern, wordbox], '^0spongKspong')
    run([wordbox, kern, glue, wordbox], '^0spong^0K spong')

    run([wordbox, math_on, wordbox], '^0spong$spong')
    run([wordbox, math_off, wordbox], '^0spong$spong')

    run([wordbox, math_on, glue, wordbox], '^0spong$ spong')
    run([wordbox, math_off, glue, wordbox], '^0spong^0$ spong')

    run([wordbox, penalty, wordbox], '^0spong^20Pspong')
    run([wordbox, penalty, glue, wordbox], '^0spong^20P spong')

    run([wordbox, discretionary, wordbox], '^0spongD^50spong')
    run([wordbox, discretionary, glue, wordbox], '^0spongD^50^0 spong')

    # XXX The penalty for discretionary hyphens is changed using
    # \hyphenpenalty and \exhyphenpenalty. Currently these have to
    # be specified to HBox.append() as optional parameters, which
    # is pretty daft. Boxes should know what document they're from.
    # When they do, we should test that here too. See issue #50.

    # whatsits add no extra breakpoints
    run([wordbox, whatsit, wordbox], '^0spongWspong')
    run([wordbox, whatsit, glue, wordbox], '^0spongW^0 spong')

def test_box_init_from_tokeniser():

    with io.StringIO("hello") as f:
        s = yex.document.Document()
        t = yex.parse.Tokeniser(s, f)

        with pytest.raises(yex.exception.YexError):
            box = yex.box.Box(t)

def test_tex_logo_p66(capsys, ):

    string = r"\setbox0=" + TEX_LOGO + r"\showbox0"

    expected = (
            r'\hbox(6.83331+2.15277)x18.6108' '\n'
            r'.\tenrm T' '\n'
            r'.\kern -1.66702' '\n'
            r'.\hbox(6.83331+0.0)x6.80557, shifted 2.15277' '\n'
            r'..\tenrm E' '\n'
            r'.\kern -1.25' '\n'
            r'.\tenrm X' '\n'
            )

    assert run_code(
            string,
            mode='horizontal',
            find='chars',
            )==''

    found = capsys.readouterr().out

    logger.debug('-- Found')
    logger.debug(found)
    logger.debug('-- Expected')
    logger.debug(expected)

    assert found.split('\n') == expected.split('\n')

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

def test_box_slicing():
    hb = yex.box.HBox()

    for width in [1, 2, 3, 4]:
        hb.append(yex.box.Box(width=width, height=1, depth=1))

    def describe(box):
        return '-'.join([str(int(x.width)) for x in box.contents])

    assert describe(hb)=='1-2-3-4'
    assert describe(hb[1:])=='2-3-4'
    assert describe(hb[2:])=='3-4'
    assert describe(hb[:3])=='1-2-3'
    assert describe(hb[:1])=='1'
    assert describe(hb[-2:])=='3-4'
    assert describe(hb[-3:-1])=='2-3'
    assert describe(hb[0:-1:2])=='1-3'

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

        assert len(found)==2, f"{cmd} / {found}"
        assert isinstance(found[0], yex.box.Rule), f"{cmd} / {found[0]}"
        assert found[0].width  == to_pt(expect_w), f"{cmd} w"
        assert found[0].height == to_pt(expect_h), f"{cmd} h"
        assert found[0].depth  == to_pt(expect_d), f"{cmd} d"
        assert found[1].ch=='q', cmd

def test_hskip_vskip():

    for form in ['hskip', 'vskip']:
        found = run_code(
                fr"\{form} 1.0pt plus 2.0pt minus 0.5pt",
                find='saw')

        assert isinstance(found[0], yex.box.Leader)
        assert found[0].width==yex.value.Dimen(1.0, 'pt')
        assert found[0].space==yex.value.Dimen(1.0, 'pt')
        assert found[0].stretch==yex.value.Dimen(2.0, 'pt')
        assert found[0].shrink==yex.value.Dimen(0.5, 'pt')

def test_hfill_etc():

    for form, expect_stretch, expect_shrink in [

            (r'\hfil',     '1.0fil',   '0.0pt'),
            (r'\hfill',    '1.0fill',  '0.0pt'),
            (r'\hfilll',   '1.0filll', '0.0pt'),
            (r'\hss',      '1.0fil',   '1.0fil'),
            (r'\hfilneg',  '-1.0fil',  '0.0pt'),

            (r'\vfil',     '1.0fil',   '0.0pt'),
            (r'\vfill',    '1.0fill',  '0.0pt'),
            # there is no \vfilll
            (r'\vss',      '1.0fil',   '1.0fil'),
            (r'\vfilneg',  '-1.0fil',  '0.0pt'),

            ]:

        found = run_code(form,
                find='saw')

        assert isinstance(found[0], yex.box.Leader)

        assert found[0].width==0, form
        assert found[0].space==0, form

        assert str(found[0].stretch)==expect_stretch, form
        assert str(found[0].shrink)==expect_shrink, form

def test_box_slice_indexing():

    hb1 = yex.box.HBox([
        yex.box.Box(width=10, height=1, depth=0),
        yex.box.Leader(space=20),
        yex.box.Box(width=30, height=1, depth=0),
        yex.box.Leader(space=40),
        yex.box.Box(width=50, height=1, depth=0),
        ])

    def examine(found, expected):

        def munge(n):
            return n.width

        assert isinstance(found, yex.box.HBox), found
        assert [munge(b) for b in found.contents]==expected, found
        assert len(found)==len(expected), found

        for i in range(-len(found), len(found)):
            assert munge(found[i])==expected[i], found

    examine(hb1, expected=[10, 20, 30, 40, 50])
    examine(hb1[:2], expected=[10, 20])
    examine(hb1[-2:], expected=[40, 50])

    hb2 = hb1[:3]
    examine(hb2, expected=[10, 20, 30])
    examine(hb2[:2], expected=[10, 20])

    hb3 = hb2[-2:]
    examine(hb3, expected=[20, 30])
    examine(hb3[:2], expected=[20, 30])

    hb4 = hb1[-3:]
    examine(hb4, expected=[30, 40, 50])
    examine(hb4[:2], expected=[30, 40])
    hb4 = hb4[:-1]
    examine(hb4, expected=[30, 40])
    examine(hb4[:2], expected=[30, 40])

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
