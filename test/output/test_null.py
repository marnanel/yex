import pytest
import yex
from test import *

def test_output_null():

    doc = yex.Document()
    output = yex.output.Output.driver_for(
            doc=doc,
            filename=None,
            )

    assert isinstance(output, yex.output.Null)

    output.render() # no error

    run_code(r'\shipout\hbox{a}', doc=doc)
    doc.save()

    with pytest.raises(yex.exception.YexError):
        output.render()
