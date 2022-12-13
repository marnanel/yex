import logging
import yex
from test import *

logger = logging.getLogger('yex.general')

def test_kern_getstate():
    g = yex.box.Kern(yex.value.Dimen(123, 'pt'))
    assert g.__getstate__()=={'kern': 123*65536}

def test_special():

    def run(code, expected):
        doc = yex.Document()

        run_code(r'\shipout\hbox{'+code+'}',
                doc=doc)
        doc.save()

        found = [x() for x in
                doc.output.found[0][0]
                if isinstance(x, yex.box.Whatsit)]

        assert len(found)==1, code
        assert (found[0][0], repr(found[0][1]))==expected, code

    def token_names_for(s):
        return '['+', '.join([f'the letter {x}' for x in s])+']'

    run(r"\special{duck soup}",
            ('duck', token_names_for('soup')),
            )

    run(r"\special{}",
            ('', '[]'),
            )

    run(r"\special{bananas}",
            ('bananas', '[]'),
            )

    run(r"\def\bananas{oranges}\special{delicious \bananas}",
            ('delicious', token_names_for('oranges')),
            )
