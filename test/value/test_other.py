import io
import pytest
from mex.state import State
from mex.parse import Token, Tokeniser, Expander
from mex.value import Number, Dimen, Glue
import mex.exception
from .. import *
import mex.put
import mex.box
import logging

general_logger = logging.getLogger('mex.general')

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
                        Dimen(i*10*65536),
                        Dimen((i*10+5)*65536),
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
        assert expand(
                r"\the\parshape",
                state = state,
                )==str(n)

    string = r'\parshape 0q'
    with expander_on_string(string, state) as e:
        token = e.next()

        assert token.ch=='q', f"final 'q' missing for {string}"

    assert state.parshape is None

    # And the count can't be negative.
    with pytest.raises(mex.exception.MexError):
        expand(
                r"\parshape -1",
                state = state,
                )
