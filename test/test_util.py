import yex
from yex.util import *
import yex.parse
from test import *

def test_put_internal_after_other_internals():

    class Thing(yex.parse.Internal):
        def __init__(self, ch):
            self.ch = ch

        def __call__(self, tokens):
            tokens.push(self.ch)

        def __repr__(self):
            return f"[Thing {self.ch}]"

    def contents_of(e):
        return ''.join([str(t) for t in e.another(on_eof='exhaust')])

    with expander_on_string("") as e:
        e.push('wombat')
        e.push(Thing('3'))
        e.push(Thing('2'))
        put_internal_after_other_internals(e, Thing('1'))

        assert contents_of(e)=='231wombat', \
                'pushes after other internals'

    with expander_on_string("") as e:
        e.push(Thing('3'))
        e.push(Thing('2'))
        put_internal_after_other_internals(e, Thing('1'))

        assert contents_of(e)=='231', 'eof is a non-internal'

    with expander_on_string("") as e:
        e.push(yex.parse.Letter('q'))
        e.push(Thing('3'))
        e.push(Thing('2'))
        put_internal_after_other_internals(e, Thing('1'))

        assert contents_of(e)=='231q', \
                'non-internal tokens aren\'t internal'

    with expander_on_string("") as e:
        put_internal_after_other_internals(e, Thing('1'))

        assert contents_of(e)=='1', 'works on empty string'

    with expander_on_string("") as e:
        e.push('wombat')
        put_internal_after_other_internals(e, Thing('1'))

        assert contents_of(e)=='1wombat', \
                'works even if no internals are waiting'
