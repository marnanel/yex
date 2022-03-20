import yex.put
import pytest

@pytest.mark.xfail
def test_put_simple():
    assert yex.put.put('wombat', catch=False)=='wombat'
