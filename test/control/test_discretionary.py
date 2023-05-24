import pytest
from test import *
import yex.box
import yex.exception

def test_inputlineno():
    string = (
            r"\discretionary{1}{2}{3}"
            )

    found = run_code(string,
            mode='dummy',
            find='saw_all',
            )

    assert len(found)>0
    result = found[0]

    assert isinstance(result, yex.box.DiscretionaryBreak)
    for found, expected in [
            (result.prebreak, '1'),
            (result.postbreak, '2'),
            (result.nobreak, '3'),
            ]:
        found = ' '.join([x.ch for x in found])

        assert found==expected

    # But you do need the braces.

    string = (
            r"\discretionary 123"
            )

    with pytest.raises(yex.exception.YexError):
        found = run_code(string,
                mode='dummy',
                )
