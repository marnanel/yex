import logging
from yex.parse import Tokeniser, Control
from yex.parse.source import FileSource
import yex.parse.token
import yex.document
from test import *

logger = logging.getLogger('yex.general')

def _check_line_status(string):
    """
    Creates a Tokeniser, and asserts that it's in line status "N".
    Then, for every Token produced by tokenising "string", adds
    the token's "ch" property and the Tokeniser's line status
    to the result string. Finally, it returns the result string.
    """
    s = yex.document.Document()
    t = Tokeniser(doc=s, source=string)

    result = ''
    for token in t:
        if token is None: break
        result += t.line_status + token.ch

    return result

def _test_tokeniser(
        text,
        expected,
        s = None,
        ):

    if s is None:
        s = yex.document.Document()

    result = []

    t = Tokeniser(doc=s, source=text)
    for item in t:
        if item is None:
            break

        if isinstance(item, Control):
            line = str(item)

        else:

            try:
                codepoint = ord(item.ch)
                if codepoint<32:
                    the_char = ''
                else:
                    the_char = f'({item.ch})'
            except TypeError:
                codepoint = 0
                the_char = f'({item.ch})'

            line ='%6d %3s %s' % (
                codepoint,
                the_char,
                item.meaning,
                )

        result.append(line)

    if result[-1]=='    32 ( ) blank space  ':
        # extra \r at EOF
        result = result[:-1]

    assert result == expected
    return result

def test_tokeniser_simple():
    assert _check_line_status(
            "Aa Bb\nCc"
            )=="NAMaM SBMbM NCMcM "

def test_tokeniser_comment():
    assert _check_line_status(
            "What% is this\rso?"
            )=="NWMhMaMtNsMoM?M "

def test_tokeniser_simple_create():
    s = yex.document.Document()
    t = Tokeniser(s, [])
    assert t is not None

def test_tokeniser_simple_text():

    _test_tokeniser(
            text = "fred123$",
    expected = [
        '   102 (f) the letter f',
        '   114 (r) the letter r',
        '   101 (e) the letter e',
        '   100 (d) the letter d',
        '    49 (1) the character 1',
        '    50 (2) the character 2',
        '    51 (3) the character 3',
        '    36 ($) math shift character $',
        ],
    )

def test_tokeniser_push_back():
    _test_tokeniser(
            text = r"\loop\iftrue",
    expected = [
        r'\loop',
        r'\iftrue',
        ],
    )

def test_tokeniser_push_back_string():
    doc = yex.Document()

    result = ''
    done_the_push = False
    string = 'ab'
    t = Tokeniser(doc=doc, source=string)

    for c in t:
        if c is None:
            break
        result += c.ch

        if not done_the_push:
            t.push("hey")
            done_the_push = True

    assert result=='aheyb '

def test_tokeniser_caret():

    s = yex.document.Document()
    s[r'\catcode00'] = 11

    _test_tokeniser(
            text = "a^^@b",
            expected = [
                '    97 (a) the letter a',
                '     0     the letter \x00',
                '    98 (b) the letter b',
                ],
            s = s,
            )

    _test_tokeniser(
            text = "a^b",
            expected = [
                '    97 (a) the letter a',
                '    94 (^) superscript character ^',
                '    98 (b) the letter b',
                ],
            )

    _test_tokeniser(
            text = "a^^6fb",
            expected = [
                '    97 (a) the letter a',
                '   111 (o) the letter o',
                '    98 (b) the letter b',
                ],
            )

    _test_tokeniser(
            text = "a^^6=b",
            expected = [
                '    97 (a) the letter a',
                '   118 (v) the letter v',
                '    61 (=) the character =',
                '    98 (b) the letter b',
                ],
            )

    _test_tokeniser(
            text = "a^^Ab",
            expected = [
                '    97 (a) the letter a',
                '     1     the character \x01',
                '    98 (b) the letter b',
                ],
            )

    _test_tokeniser(
            text = r"\d^^6fg",
            expected = [
                r'\dog',
                ],
            )

def test_tokeniser_active_characters():
    _test_tokeniser(
            text = "R.~J. Drofnats",
            expected = [
                '    82 (R) the letter R',
                '    46 (.) the character .',
                '   126 (~) the active character ~',
                '    74 (J) the letter J',
                '    46 (.) the character .',
                '    32 ( ) blank space  ',
                '    68 (D) the letter D',
                '   114 (r) the letter r',
                '   111 (o) the letter o',
                '   102 (f) the letter f',
                '   110 (n) the letter n',
                '    97 (a) the letter a',
                '   116 (t) the letter t',
                '   115 (s) the letter s',
                ],
            )

def eat_optional_something(
        text,
        call,
        ):
    doc = yex.Document()
    t = Tokeniser(doc=doc, source=text)

    returned = []
    eaten = []

    for c in t:
        if c is None:
            break

        returned.append(c)
        eaten.append(call(t))

    return list(zip(returned, eaten))

def test_tokeniser_eat_optional_spaces():
    found = eat_optional_something(
            text = 'a         bc',
            call = lambda t: t.eat_optional_spaces(),
            )
    assert found==[
            (yex.parse.Letter('a'), [yex.parse.Space(ch=' ')]),
            (yex.parse.Letter('b'), []),
            # EOF is equivalent to a space:
            (yex.parse.Letter('c'), [yex.parse.Space(ch=' ')]),
            ]

def test_tokeniser_eat_optional_char():
    found = eat_optional_something(
            text = 'ab=c==d===e',
            call = lambda t: t.eat_optional_char('='),
            )
    assert found==[
            (yex.parse.Letter(ch='a'), None),

            (yex.parse.Letter(ch='b'), yex.parse.Other(ch='=')),

            (yex.parse.Letter(ch='c'), yex.parse.Other(ch='=')),
            (yex.parse.Other(ch='='),  None),

            (yex.parse.Letter(ch='d'), yex.parse.Other(ch='=')),
            (yex.parse.Other(ch='='),  yex.parse.Other(ch='=')),

            (yex.parse.Letter(ch='e'), None),
            (yex.parse.Space(ch=' '),  None),
            ]

def test_tokeniser_optional_string():
    s = yex.document.Document()

    text = r'\red papaya\green'

    result = []

    t = Tokeniser(doc=s, source=text)

    for c in t:
        result.append(
                (repr(c), t.optional_string("paya")),
                )
        if c is None:
            break

    assert result==[
            (r'\red', False),
            (r'the letter p', False),
            (r'the letter a', True),
            (r'\green', False),
            (r'None', False),
            ]

def test_ascii_lookup():
    """
    Tests the various ways of getting ASCII code information.

    See the TeXbook, p43f.
    """
    assert run_code(r'\char98',   find='chars')=='b'
    assert run_code(r"\char'142", find='chars')=='b'
    assert run_code(r'\char"62',  find='chars')=='b'

def test_tokeniser_location(fs):

    FILENAME = 'wombat.tex'
    CONTENTS = 'abc\rd\refg'

    fs.create_file(FILENAME,
            contents = CONTENTS)

    with open(FILENAME, 'r') as f:

        doc = yex.document.Document()

        tokeniser = Tokeniser(
                doc = doc,
                source = f,
                )

        assert tokeniser.location.line==0
        assert tokeniser.location.column==1
        assert tokeniser.location.filename==FILENAME

        result = []
        for token in tokeniser:
            if token is None:
                break

            result.append("%s%d%d" % (
                token.ch,
                token.location.line,
                token.location.column,
                ))

            assert tokeniser.location.filename==FILENAME
            assert token.location.filename==FILENAME

        assert result==[
                'a11', 'b12', 'c13', ' 14',
                'd21', ' 22',
                'e31', 'f32', 'g33', ' 34',
                ]

def test_tokeniser_from_tokenlist():

    doc = yex.Document()

    tokens = [yex.parse.Letter(c) for c in "wombat"]
    tokens.append(yex.parse.Control(r"\par",
        doc=doc, location=None))

    tl = yex.value.Tokenlist(tokens)

    tokeniser = Tokeniser(doc=doc, source=tl)

    result = [t for t in yex.parse.Expander(tokeniser, on_eof='exhaust')]

    assert result==tokens

def test_issue71_comment_to_eol():

    F_IS_A_NEWLINE = r"\catcode`F=5" # F is now a newline character
    CR_IS_AN_O = r"\catcode`\^^M=13\def^^M{o}"
    P_IS_A_COMMENT = r"\catcode`P=14"

    assert run_code(
                find = 'ch',
                setup = CR_IS_AN_O,
        call = r"""one

two % but this bit never shows up and also doesn't cause the entire
% rest of the file to be interpreted as a comment despite the fact
% that carriage returns are no longer carriage returns

three

four""",
)=='oneootwo othreeoofouro', (
        'redefining ^M doesn\'t cause comments to run on forever'
        )

    assert run_code(
        find = 'ch',
        setup = F_IS_A_NEWLINE,
        call = (
            r"QRF all this is after the EOL so doesn't appear" "\n"
            r"STF even if it contains another F character" "\n"
            r"UVF and even if it contains a % sign" "\n"
            r"WXF but it becomes whitespace instead" "\n"
            r"But what about if it goes FF?" "\n"
            r"F and this will cause a \par" "\n"
            r"Let's see." "\n"
            ))=='QR ST UV WX But what about if it goes \\parLet\'s see.', (
                    'EOL causes the rest of the line to be ignored'
                    )

    assert run_code(
            find = 'ch',
            setup = P_IS_A_COMMENT,
            call = (
                r"QRP again, all this doesn't appear" "\n"
                r"STP even if it contains another P character" "\n"
                r"UVP and even if it contains a % sign" "\n"
                r"WXP and it *doesn't* become whitespace instead" "\n"
                r"But what about if it goes PP?" "\n"
                r"P and this *won't* cause a \par" "\n"
                r"Let's see." "\n"
                ))=='QRSTUVWXBut what about if it goes Let\'s see.', (
                        'EOL causes the rest of the line to be ignored'
                        )

def test_tokeniser_group_depth():

    S = [
            ('A', 0),
            ('{', 1),
            ('B', 1),
            ('C', 1),
            ('{', 2),
            ('D', 2),
            ('}', 1),
            ('E', 1),
            ('}', 0),
            ('F', 0),
            ]

    doc = yex.Document()
    t = Tokeniser(doc, ''.join([a for a,b in S]))

    def run_forwards():
        tokens = []
        for s, token in zip(S, t):
            assert token.ch==s[0], s
            assert t.pushback.group_depth==s[1], s
            tokens.append(token)

        return tokens

    def run_backwards(items):
        for s, item in zip(reversed(S), reversed(items)):
            assert t.pushback.group_depth==s[1], (s, item)
            t.push(item)

    tokens = run_forwards()
    run_backwards(tokens)

def test_tokeniser_macros_named_curly_brackets():

    for string in [
            r"\def\a{}",
            r"\def\{{}",
            r"\def\}{}",
            ]:
        e = run_code(
                string,
                find='expander',
                )

        assert e.pushback.group_depth==0, string

def test_tokeniser_triptest_line82():
    # Regression test.
    # This had been failing because the \fi at the end of the first line
    # was terminated by a newline. yex knew to absorb a space after a
    # literal control name, but not to absorb a newline. So it went on
    # trying to parse the number that was introduced by the double-quote
    # mark, and complained that numbers can't begin with a newline.
    assert run_code(
            call = (
                r"\if00-0.\fi\ifnum'\ifnum10=10" r' 12="\fi' '\n'
                r"A 01p\ifdim1,0pt<`^^Abpt\fi\fi"
                ),
            find = 'ch',
            ) =='-0.01pt'

def test_tokeniser_whitespace_after_control_words():

    found = run_code(
            setup = r'\def\a{g}',
            call = (
            r'\a    \a' '\r'
            r'\a' '\r'
            r'b'
            ),
            find='chars',
            )

    assert found=='gggb'

def create_incoming():
    pushback = yex.parse.Pushback()

    pushback.push(
            yex.parse.Letter(
                ch = 'M',
                location = yex.parse.Location(
                    filename = 'wombat.tex',
                    line = 100,
                    column = 200,
                    ),
                )
            )

    pushback.push(
            yex.parse.Other(
                ch = '?',
                location = yex.parse.Location(
                    filename = 'argle.tex',
                    line = 400,
                    column = 500,
                    ),
                )
            )

    source = yex.parse.source.StringSource(
            "Hello world!",
            )
    incoming = yex.parse.Incoming(
            pushback = pushback,
            source = source,
            )
    return incoming

def test_incoming_simple():
    incoming = create_incoming()

    found = ''

    for item in incoming:
        if item is None:
            break
        found += str(item)

    assert found.strip() == '?MHello world!'

def test_incoming_location():
    incoming = create_incoming()

    tahvo = yex.parse.Letter(
                ch = 'T',
                location = yex.parse.Location(
                    filename = 'tahvo.tex',
                    line = 600,
                    column = 700,
                    ),
                )

    EXPECTED = [
            'argle.tex:400:500',
            'wombat.tex:100:200',
            '<str>:0:1',
            '<str>:1:1',
            '<str>:1:2',
            '<str>:1:3',
            '<str>:1:4',
            '<str>:1:5',
            '<str>:1:6',
            # (here we insert tahvo, then remove it)
            '<str>:1:6',
            '<str>:1:7',
            '<str>:1:8',
            '<str>:1:9',
            '<str>:1:10',
            '<str>:1:11',
            '<str>:1:12',
            '<str>:1:13',
            '<str>:1:14',
            ]

    tokens = [
    ]

    assert str(incoming.location) == EXPECTED[0], repr(item)
    for expected, item in zip(EXPECTED[1:], incoming):
        if item=='\r':
            continue
        elif item is None:
            break

        assert str(incoming.location) == expected, repr(item)

        tokens.append(item)

        if item==' ':
            # arbitrary, somewhere in the middle of the list
            incoming.pushback.push(tahvo)
            assert str(incoming.location) == 'tahvo.tex:600:700'
