import io
import mex.filename
import mex.token
import mex.state

def test_filename_simple():

    s = mex.state.State()

    string = r'wombat foo'
    with io.StringIO(string) as f:
        t = mex.token.Tokeniser(
                state = s,
                source = f,
                )

        fn = mex.filename.Filename(
                tokens = t,
                )

        assert fn.value == 'wombat'
