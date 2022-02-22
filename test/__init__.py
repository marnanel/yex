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

def _get_number(number,
        state = None):
    """
    Creates a State and a Tokeniser, and tokenises the string
    you pass in. The string should represent a number followed
    by the letter "q" (so we can test how well numbers are
    delimited by the following characters).

    Returns the number.
    """

    if state is None:
        state = mex.state.State()

    with io.StringIO(number) as f:
        t = mex.parse.Tokeniser(state, f)

        result = mex.value.Number(t)

        try:
            q = t.__next__()
        except StopIteration:
            raise ValueError("Wanted trailing 'q' for "
                    f"{number} but found nothing")

        if q.category==q.LETTER and q.ch=='q':
            return result.value
        else:
            raise ValueError(f"Wanted trailing 'q' for "
                    f"{number} but found {q}")

def _get_dimen(dimen,
        state = None):
    """
    Creates a State and a Tokeniser, and tokenises the string
    you pass in. The string should represent a dimen followed
    by the letter "q" (so we can test how well numbers are
    delimited by the following characters).

    If you supply a State, we use that State rather than
    creating a throwaway State.

    Returns the size in scaled points.
    """

    if state is None:
        state = mex.state.State()

    with io.StringIO(dimen) as f:
        t = mex.parse.Tokeniser(state, f)

        result = mex.value.Dimen(t)

        try:
            q = t.__next__()
        except StopIteration:
            raise ValueError("Wanted trailing 'q' for "
                    f"{dimen} but found nothing")

        if q.category==q.LETTER and q.ch=='q':
            return result.value
        else:
            raise ValueError(f"Wanted trailing 'q' for "
                    f"{dimen} but found {q}")

def _get_glue(glue,
        state = None,
        raw = False):
    """
    Creates a State and a Tokeniser, and tokenises the string
    you pass in. The string should represent a Glue followed
    by the letter "q" (so we can test how well Glues are
    delimited by the following characters).

    If you supply a State, we use that State rather than
    creating a throwaway State.

    Returns a tuple: (space, stretch, shrink).
    """

    if state is None:
        state = mex.state.State()

    with io.StringIO(glue) as f:
        t = mex.parse.Tokeniser(state, f)

        result = mex.value.Glue(t)

        try:
            q = t.__next__()
        except StopIteration:
            raise ValueError("Wanted trailing 'q' for "
                    f"{dimen} but found nothing")

        if q.category==q.LETTER and q.ch=='q':
            if raw:
                return result

            return (
                    result.space.value,
                    result.stretch.value,
                    result.shrink.value,
                    result.stretch.infinity,
                    result.shrink.infinity,
                    )
        else:
            raise ValueError(f"Wanted trailing 'q' for "
                    f"{glue} but found {q}")

__all__ = [
        '_test_expand',
        '_get_number',
        '_get_dimen',
        '_get_glue',
        ]
