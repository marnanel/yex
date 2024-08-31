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
            return result

        for i in range(peek_count):
            if i==0:
                found_from_peek = what.peek()
            else:
                assert what.peek()==found_from_peek

        result.append(item)

    return result

def test_peek():
    def string_source():
        return yex.parse.StringSource(
                string = STRING_SOURCE_SEND,
                )
    assert roll_through(string_source(), 0)==STRING_SOURCE_EXPECTED
    assert roll_through(string_source(), 1)==STRING_SOURCE_EXPECTED
    assert roll_through(string_source(), 4)==STRING_SOURCE_EXPECTED

STRING_SOURCE_SEND = (
                    'Hello\n'
                    'world.'
                    )

STRING_SOURCE_EXPECTED = [
        'H', 'e', 'l', 'l', 'o', '\r', 'w', 'o', 'r', 'l', 'd', '.', '\r',
        ]
