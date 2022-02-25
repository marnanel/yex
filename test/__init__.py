import io
import mex.parse
import mex.state
import mex.value

def _test_expand(string, s=None, *args, **kwargs):

    if s is None:
        s = mex.state.State()

    with io.StringIO(string) as f:
        t = mex.parse.Tokeniser(
                state = s,
                source = f,
                )

        e = mex.parse.Expander(t,
                *args, **kwargs)

        result = ''.join([t.ch for t in e])

    return result

def _test_call_macro(
        setup,
        call,
        state = None,
        as_list = False,
        ):

    if state is None:
        state = mex.state.State()

    _test_expand(setup, s=state)

    with io.StringIO(call) as f:
        t = mex.parse.Tokeniser(
                state = state,
                source = f,
                )

        for name in t:
            break

        result = state[name.name](
                name = name.name,
                tokens = t)

        if not as_list:
            result = ''.join([
                x.ch for x in result
                ])

        return result

def _tokenise_and_get(string, cls, state = None):
    """
    Creates a State and a Tokeniser, and initialises the
    class "cls" with that Tokeniser.

    The string should represent the new value followed
    by the letter "q" (so we can test how well literals are
    delimited by the following characters).

    If you pass in "state", uses that State instead of
    constructing a new one.

    Returns the result.
    """

    if state is None:
        state = mex.state.State()

    with io.StringIO(string) as f:
        t = mex.parse.Tokeniser(state, f)

        result = cls(t)

        try:
            for q in t:
                break
        except StopIteration:
            raise ValueError("Wanted trailing 'q' for "
                    f'"{string}" but found nothing')

        if not (q.category==q.LETTER and q.ch=='q'):
            raise ValueError(f"Wanted trailing 'q' for "
                    f'"{string}" but found {q}')

        return result

def _get_number(string,
        state = None):
    """
    See _tokenise_and_get().
    """

    result = _tokenise_and_get(string,
            cls=mex.value.Number,
            state=state)

    return result.value

def _get_dimen(string,
        state = None):
    """
    See _tokenise_and_get().
    """


    result = _tokenise_and_get(string,
            cls=mex.value.Dimen,
            state=state)

    return result.value

def _get_glue(string,
        state = None,
        raw = False):
    """
    See _tokenise_and_get().

    If raw is True, returns the Glue object;
    otherwise returns a tuple:
       (space, stretch, shrink, stretch_infinity,
       shrink_infinity).
    """

    result = _tokenise_and_get(string,
            cls=mex.value.Glue,
            state=state)

    if raw:
        return result

    return (
            result.space.value,
            result.stretch.value,
            result.shrink.value,
            result.stretch.infinity,
            result.shrink.infinity,
            )

def _get_muglue(string,
        state = None,
        raw = False):
    """
    See _tokenise_and_get().

    If raw is True, returns the Muglue object;
    otherwise returns a tuple:
       (space, stretch, shrink, stretch_infinity,
       shrink_infinity).
    """

    result = _tokenise_and_get(string,
            cls=mex.value.Muglue,
            state=state)

    if raw:
        return result

    return (
            result.space.value,
            result.stretch.value,
            result.shrink.value,
            result.stretch.infinity,
            result.shrink.infinity,
            )

__all__ = [
        '_test_expand',
        '_get_number',
        '_get_dimen',
        '_get_glue',
        '_get_muglue',
        ]
