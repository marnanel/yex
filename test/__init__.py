import io
import mex.parse
import mex.state
import mex.value
import logging
import contextlib

general_logger = logging.getLogger('mex.general')

def expand(string, state=None,
        *args, **kwargs):

    # FIXME at some point, rewrite all the calls to this function
    # in terms of call_macro()

    if 's' in kwargs:
        # Workaround for old tests; should fix at some point
        state = kwargs['s']
        del kwargs['s']

    return call_macro(
            call=string,
            state=state,
            )

def call_macro(
        setup = None,
        call = '',
        state = None,
        as_list = False,
        ):
    """
    Runs the TeX code in "setup" and throws away the result.
    Then, runs through the code in "call", using an Expander
    with expand=False. When call_macro() gets a Token back
    which is a control word which represents an existing
    Control, it calls that Control itself (rather than
    expecting the Expander to do it).

    This means that the results of macros are seen, rather
    than the results of results (of results...) of macros.
    In particular, it means we see whether a macro produces
    { or }.

    Note that we don't handle active characters (though
    we probably should.)

    If state!=None, uses it; otherwise, creates a new State.

    If as_list==True, returns the Tokens received as a list.
    Otherwise, returns a string made of concatenating the
    "ch" values of all the Tokens received.
    """

    if state is None:
        state = mex.state.State()

    if setup is not None:
        general_logger.debug("=== call_macro sets up: %s ===",
                setup)

        result = expand(setup, s=state)

        if result!='':
            general_logger.debug((
                "call_macro received from setup: %s "
                "(but we throw it away)"
                ),
                result)

    result = []

    with io.StringIO(call) as f:
        t = mex.parse.Tokeniser(
                state = state,
                source = f,
                )
        e = mex.parse.Expander(t,
                expand = False,
                )

        general_logger.debug("=== call_macro begins: %s ===",
                call)

        for token in e:

            general_logger.debug("call_macro saw: %s",
                    token)

            if token.category!=token.CONTROL:
                general_logger.debug("  -- which isn't a control; saved to result")

                result.append(token)
                continue

            name = token.name

            try:
                handler = state[name]
            except KeyError:
                # FIXME when State.__contains__ is implemented,
                # we should use it here.
                general_logger.debug("  -- which isn't known; saved to result")
                result.append(token)
                continue

            general_logger.debug("  -- calling it")
            received = handler(
                    name = token,
                    tokens = e,
                    )
            if received is None:
                general_logger.debug(r"call_macro: \%s gave us None",
                        name,
                        )
            else:
                result.extend(received)

                general_logger.debug(r"call_macro: \%s gave us %s; saved to result",
                        name,
                        received,
                        )

    if not as_list:
            result = ''.join([
                x.ch for x in result
                ])

    general_logger.debug("=== call_macro result: %s ===",
            result)

    return result

def tokenise_and_get(string, cls, state = None):
    """
    Creates a State, a Tokeniser, and an Expander,
    and initialises the class "cls" with that Expander.

    The string should represent the new value followed
    by the letter "q" (so we can test how well literals are
    delimited by the following characters).

    If you pass in "state", uses that State instead of
    constructing a new one.

    Returns the result.
    """

    if state is None:
        state = mex.state.State()

    with expander_on_string(string, state,
            expand=False) as e:

        result = cls(e)

        for q in e:
            break

        if q is None:
            raise ValueError("Wanted trailing 'q' for "
                    f'"{string}" but found nothing')

        if not (q.category==q.LETTER and q.ch=='q'):
            raise ValueError(f"Wanted trailing 'q' for "
                    f'"{string}" but found {q}')

        return result

def get_number(string,
        state = None,
        raw = False,
        ):
    """
    See tokenise_and_get().
    """

    result = tokenise_and_get(string,
            cls=mex.value.Number,
            state=state,
            )

    if raw:
        return result

    return result.value

def get_dimen(string,
        state = None,
        raw = False,
        ):
    """
    See tokenise_and_get().
    """

    result = tokenise_and_get(string,
            cls=mex.value.Dimen,
            state=state,
            )

    if raw:
        return result

    return result.value

def get_glue(string,
        state = None,
        raw = False):
    """
    See tokenise_and_get().

    If raw is True, returns the Glue object;
    otherwise returns a tuple:
       (space, stretch, shrink, stretch_infinity,
       shrink_infinity).
    """

    result = tokenise_and_get(string,
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

def get_muglue(string,
        state = None,
        raw = False):
    """
    See tokenise_and_get().

    If raw is True, returns the Muglue object;
    otherwise returns a tuple:
       (space, stretch, shrink, stretch_infinity,
       shrink_infinity).
    """

    result = tokenise_and_get(string,
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

def compare_strings_with_reals(
        left, right, tolerance=0.1,
        ):
    import re

    real = re.compile(r"([0-9]+(?:\.[0-9]+)?)")

    left = real.split(left)
    right = real.split(right)

    assert len(left)==len(right)

    for l, r in zip(left, right):
        try:
            l = float(l)
            r = float(r)
            assert abs(l-r)<=tolerance, "l != r"
        except ValueError:
            assert l==r

@contextlib.contextmanager
def expander_on_string(string, state=None,
        *args, **kwargs):

    with io.StringIO(string) as f:

        if state is None:
            state = mex.state.State()

        t = mex.parse.Tokeniser(state, f)
        e = mex.parse.Expander(t,
                *args, **kwargs)

        yield e

__all__ = [
        'expand',
        'call_macro',
        'get_number',
        'get_dimen',
        'get_glue',
        'get_muglue',
        'compare_strings_with_reals',
        'expander_on_string',
        ]
