import yex
from test import *

def test_style():
    CODE = r'This is \fmtversion'
    for (style, expected) in [
            (yex.style.Bare, CODE),
            (yex.style.Plain, 'This is 3.141592653'),
            ]:
        doc = yex.Document(
                style = style,
                )

        assert run_code(
                call=CODE,
                doc=doc,
                find='tokens',
                )==expected, style.__name__
