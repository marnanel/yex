import logging
import yex
from test import *

logger = logging.getLogger('yex.general')

def test_special():

    def run(code, expected):
        doc = yex.Document()

        found = [item for item in
                run_code(r'\shipout\hbox{'+code+'}',
                output='dummy',
                find='items',
                doc=doc)
                if isinstance(item, yex.box.Whatsit)]

        assert len(found)==1, code
        assert found[0].render()==expected, code

    def tokens_for(s):
        return [yex.parse.Letter(ch=x)
                for x in s]

    run(r"\special{duck soup}",
            ('duck', tokens_for('soup')),
            )

    run(r"\special{}",
            ('', []),
            )

    run(r"\special{bananas}",
            ('bananas', []),
            )

    run(r"\def\bananas{oranges}\special{delicious \bananas}",
            ('delicious', tokens_for('oranges')),
            )
