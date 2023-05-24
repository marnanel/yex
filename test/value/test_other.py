import io
import pytest
from yex.document import Document
from yex.value import Number, Dimen, Glue
import yex.exception
from .. import *
import yex.put
import yex.box
import logging

logger = logging.getLogger('yex.general')

def test_parshape():

    doc = Document()

    for n in range(1, 5):
        string = rf"\parshape {n}"+\
                ''.join([
                    " %dpt %dpt" % (i*10, i*10+5)
                    for i in range(1, n+1)]) +\
                "q"

        with expander_on_string(string, doc) as e:

            token = e.next()
            assert token.ch=='q', f"final 'q' missing for {string}"

            expected = [
                    (
                        Dimen(i*10),
                        Dimen((i*10+5)),
                        )
                    for i in range(1, n+1)
                    ]

            logger.debug('ST %s', string)
            logger.debug('SP %s == %s', doc.parshape,
                    [(a.value, b.value) for a,b in doc.parshape],
                    )
            logger.debug('EX %s == %s', expected,
                    [(a.value, b.value) for a,b in doc.parshape],
                    )
            assert doc.parshape == expected
            for token in e:
                break

        # But reading it back just gives us the count
        assert run_code(
                r"\the\parshape",
                doc = doc,
                find = 'chars',
                )==str(n)

    string = r'\parshape 0q'
    with expander_on_string(string, doc) as e:
        token = e.next()

        assert token.ch=='q', f"final 'q' missing for {string}"

    assert doc.parshape is None

    # And the count can't be negative.
    with pytest.raises(yex.exception.YexError):
        run_code(
                r"\parshape -1",
                doc = doc,
                )
