import yex
from test import *

def roll_through(
        what,
        peek_count,
        ):

    result = []

    for item in what:

        found_from_peek = None

        if item is None:
            return result

        for i in range(peek_count):
            assert what.peek()==item

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
