from test import *
import pytest
import yex

def test_document_normalise_name():
    nn = yex.Document._normalise_name

    assert nn('fred') == ('fred',)
    assert nn('count123') == ('count', 123)
    assert nn('count123;456') == ('count123', 456)
    assert nn('count;456') == ('count', 456)
    assert nn( ('fred',) ) == ('fred',)
    assert nn( ('fred', 123) ) == ('fred', 123)

    with pytest.raises(TypeError):
        nn( ('fred', complex ) )

    with pytest.raises(TypeError):
        nn( 123 )
