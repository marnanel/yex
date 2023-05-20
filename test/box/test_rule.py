import yex
from test import *
from yex.value import Dimen

def get_rule(s=None, direction='h', expander=None, **expect):

    if s is not None:
        doc = yex.Document()
        expander = doc.open(s)

    result = yex.box.Rule.from_tokens(expander,
            is_horizontal=(direction=='h'))

    for f,v in expect.items():
        if isinstance(v, (int,float)):
            v = Dimen(v, 'pt')
        assert getattr(result, f)==v, f'{f}=={v} in "{s}"'

    return result

def test_rule_simple():

    INH = 'inherit'

    for s, direction, width, height, depth in [
            #                                  dir  w    h     d
            ("width 2pt",                      'h', 2,   0.4,  0),
            ("height 2pt",                     'h', INH, 2,    0),
            ("depth 2pt",                      'h', INH, 0.4,  2),
            ("width 2pt depth 5pt",            'h', 2,   0.4,  5),
            ("depth 1pt width 2pt height 5pt", 'h', 2,   5,    1),
            ("width 2pt depth 5ptQQQ",         'h', 2,   0.4,  5),

            ("width 2pt",                      'v', 2,   INH,  INH),
            ("height 2pt",                     'v', 0.4, 2,    INH),
            ("depth 2pt",                      'v', 0.4, INH,  2),
            ("width 2pt depth 5pt",            'v', 2,   INH,  5),
            ("depth 1pt width 2pt height 5pt", 'v', 2,   5,    1),
            ]:

        get_rule(s, direction, width=width, height=height, depth=depth)

def test_rule_eating_text():
    doc = yex.Document()
    e = yex.parse.Expander(
            r"width 2pt department store",
            on_eof='exhaust',
            doc=doc,
            )

    rule = get_rule(None, expander=e, width=2, height=0.4, depth=0)

    remaining = ''.join([t.ch for t in e])
    assert remaining==' department store '

def test_rule_containing_control():

    found = run_code(
            setup=r"\dimen12=34pt",
            call=r"\hrule height 2pt depth\dimen12",
            find='saw_all',
            )
    assert len(found)==1
    assert isinstance(found[0], yex.box.Rule)

def test_rule_is_not_void():
    rule = get_rule('')
    assert not rule.is_void()
