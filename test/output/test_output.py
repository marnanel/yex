import yex
import pytest
from test import *

def test_get_driver_for():

    doc = yex.Document()

    def run(filename, format, expected):
        found = yex.output.Output.driver_for(doc=doc,
                filename=filename,
                format=format,
                )

        context = f'{filename} {format}'

        assert isinstance(found, expected), context
        assert found.doc==doc, context

    run(filename='wombat.html', format=None, expected=yex.output.Html)
    run(filename='wombat.svg', format=None, expected=yex.output.Svg)
    run(filename='wombat.svg', format='html', expected=yex.output.Html)
    run(filename='wombat.this-is-a-silly-extension',
            format='html', expected=yex.output.Html)

    with pytest.raises(yex.exception.YexError):
        run(filename='wombat.this-is-a-silly-extension', format=None,
                expected=None)

    with pytest.raises(yex.exception.YexError):
        run(filename='wombat.html', format='this-is-a-silly-format',
                expected=None)
