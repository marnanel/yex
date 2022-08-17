import yex
from test import *
import pytest

def test_exception_simple():
    d = yex.value.Dimen()

    with pytest.raises(yex.exception.CantAddError):
        d = d + 1
