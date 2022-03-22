import io
import pytest
from yex.state import State
from yex.value import Number, Dimen, Glue
import yex.exception
from .. import *
import yex.put
import yex.box
import logging

general_logger = logging.getLogger('yex.general')

def test_parshape():

    state = State()

    for n in range(1, 5):
        string = rf"\parshape {n}"+\
                ''.join([
                    " %dpt %dpt" % (i*10, i*10+5)
                    for i in range(1, n+1)]) +\
                "q"

        with expander_on_string(string, state) as e:

            token = e.next()
            assert token.ch=='q', f"final 'q' missing for {string}"

            expected = [
                    (
                        Dimen(i*10),
                        Dimen((i*10+5)),
                        )
                    for i in range(1, n+1)
                    ]

            general_logger.debug('ST %s', string)
            general_logger.debug('SP %s', state.parshape)
            general_logger.debug('EX %s', expected)
            assert state.parshape == expected
            for token in e:
                break

        # But reading it back just gives us the count
        assert run_code(
                r"\the\parshape",
                state = state,
                find = 'chars',
                )==str(n)

    string = r'\parshape 0q'
    with expander_on_string(string, state) as e:
        token = e.next()

        assert token.ch=='q', f"final 'q' missing for {string}"

    assert state.parshape is None

    # And the count can't be negative.
    with pytest.raises(yex.exception.YexError):
        run_code(
                r"\parshape -1",
                state = state,
                )
