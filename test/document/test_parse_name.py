from test import *
import pytest
import yex

def test_document_parse_name():
    nn = yex.Document._parse_name

    assert nn('fred', None)    == ('fred', None)
    assert nn('count123', None)      == ('count', 123)
    assert nn('count123;456', None)  == ('count123', 456)
    assert nn('count;456', None)     == ('count', 456)
    assert nn('fred', 123)     == ('fred', 123)

    with pytest.raises(ValueError):
        nn('fred123', 456)

    with pytest.raises(TypeError):
        nn('fred', complex)
