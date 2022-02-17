import mex.put
import mex.state

def test_expected_number_but_got_dimen_register():
    state = mex.state.State()
    string = r'\dimen1=100mm \count1=\dimen1'

    mex.put.put(string, state=state)
