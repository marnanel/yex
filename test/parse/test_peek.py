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

        # We break on the full stop at the end as well as None,
        # so we can test cases with on_eof!='none'.
        if item is None or repr(item)=="the character .":
            break

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
                source = STRING_SOURCE_SEND,
                ),
            expected = TOKENISER_EXPECTED,
            )

    for level in ['deep', 'reading', 'expanding', 'executing', 'querying']:
        for on_eof in ['none', 'raise', 'exhaust']:
            roll_through_0_1_4(
                    name = f'Expander({level}, {on_eof})',
                    unit_generator = lambda: yex.parse.Expander(
                        doc = doc,
                        level = level,
                        on_eof = on_eof,
                        source = yex.parse.Tokeniser(
                            doc = doc,
                            source = STRING_SOURCE_SEND,
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
        "'w'", "'o'", "'r'", "'l'", "'d'", "'.'", "'\\r'",
        ]

TOKENISER_EXPECTED = [
        'the letter H',
        'the letter e',
        'the letter l',
        'the letter l',
        'the letter o',
        'blank space  ',
        'the letter w',
        'the letter o',
        'the letter r',
        'the letter l',
        'the letter d',
        'the character .',
        ]
