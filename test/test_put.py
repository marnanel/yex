import mex.put
import pytest

@pytest.mark.xfail
def test_put_simple():
    assert mex.put.put('wombat', catch=False)=='wombat'
