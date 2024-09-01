import yex
from test import *

def roll_through(
        what,
        peek_count,
        ):

    result = []
    found_from_peek = None

    for item in what:

        if found_from_peek:
            assert item==found_from_peek

        if item is None:
            with open('/tmp/q', 'w') as f:
                f.write(repr(result))
            return result

        for i in range(peek_count):
            if i==0:
                found_from_peek = what.peek()
            else:
                assert what.peek()==found_from_peek

        result.append(repr(item))

    return result

def roll_through_0_1_4(
        name,
        unit_generator,
        expected,
        ):

    for count in [0, 1, 4]:
        assert roll_through(unit_generator(), count)==expected, (
                f"{name} {count}"
                )

def test_peek():

    doc = yex.Document()

    roll_through_0_1_4(
            name = 'StringSource',
            unit_generator = lambda: yex.parse.StringSource(
                string = STRING_SOURCE_SEND,
                ),
            expected = STRING_SOURCE_EXPECTED,
            )

    roll_through_0_1_4(
            name = 'Tokeniser',
            unit_generator = lambda: yex.parse.Tokeniser(
                doc = doc,
                source = yex.parse.StringSource(
                    string = STRING_SOURCE_SEND,
                    ),
                ),
            expected = TOKENISER_EXPECTED,
            )

STRING_SOURCE_SEND = (
                    'Hello\n'
                    'world.'
                    )

STRING_SOURCE_EXPECTED = [
        "'H'", "'e'", "'l'", "'l'", "'o'", "'\\r'",
        "'w'", "'o'", "'r'", "'l'", "'d'", "'.'", "'\\r'"
        ]

TOKENISER_EXPECTED = [
        'the character [',
        'the letter S',
        'the letter t',
        'the letter r',
        'the letter i',
        'the letter n',
        'the letter g',
        'the letter S',
        'the letter o',
        'the letter u',
        'the letter r',
        'the letter c',
        'the letter e',
        'the character ;',
        'the character <',
        'the letter s',
        'the letter t',
        'the letter r',
        'the character >',
        'the character ;',
        'the letter l',
        'the character =',
        'the character 0',
        'the character ;',
        'the letter c',
        'the character =',
        'the character 1',
        'the character ]',
        'blank space  ',
        ]
