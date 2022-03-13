import io
import mex.parse
import mex.state
import mex.value
import logging
import contextlib

general_logger = logging.getLogger('mex.general')

def run_code(
        call,
        setup = None,
        state = None,
        mode = 'vertical',
        find = None,
        strip = True,
        *args, **kwargs,
        ):
    """
    Instruments and runs some code, and returns details.

    Parameters:

        call -      TeX code to run
        setup -     TeX code to run before running "call",
                    or None to run nothing. This code is
                    run on the same State, but isn't used
                    for testing.
        state -     the State to run the code on. If None,
                    we create a new State just for this test.
        mode -      the mode to start in. Defaults to "vertical".
                    If you set this to "dummy", we splice in
                    a dummy Mode which does nothing. This lets
                    you test code which would annoy all the real modes.
        find -      affects the results you get; see below.
        strip -     if True, and the result would be a string,
                    run strip() on it before returning.
                    (Sometimes the phantom EOL at the end of a string
                    causes a Mode to insert a space.)
                    If this fails, we continue silently.

        When find is None, which is the default, the result is a dict.
        It contains at least the following entries:

        saw -       a list of everything which the Expander sent to
                    the Mode. run_code() sits between the two and
                    records it all.
        list -      the "list" attribute of the outermode Mode
                    after the test code finished.

        If find is not None, it should be a string. If it's the name
        of a field in the default result dict, we return only that field.
        Other options are:

        chars -     returns a string, the names of the non-control
                    Tokens in 'saw'. For example, a letter token for "B"
                    adds a "B" to the string.
        tokens -    like 'chars', except control Tokens are included.
                    Control tokens add their name to the string,
                    like "\par".
        ch -        like 'chars', except everything is included.
                    Whatever the token's 'ch' method returns gets added.

        Some of these options have unhelpful names.
    """
    if state is None:
        state = mex.state.State()

    if mode=='dummy':
        class DummyMode:
            def __init__(self, state):
                self.state = state
                self.name = 'dummy'
                self.list = []

            def handle(self, item, tokens):
                general_logger.debug("dummy mode saw: %s",
                        item)

        state.controls['_mode'].mode_handlers[mode]=DummyMode

    state['_mode'] = mode

    if setup is not None:
        general_logger.debug("=== run_code sets up: %s ===",
                setup)

        t = mex.parse.Tokeniser(
                state = state,
                source = setup,
                )
        e = mex.parse.Expander(t,
                *args, **kwargs,
                )

        for item in e:
            state.mode.handle(
                    item = item,
                    tokens = e,
                    )

    general_logger.debug("=== run_code begins: %s ===",
            call)

    t = mex.parse.Tokeniser(
            state = state,
            source = call,
            )
    e = mex.parse.Expander(t,
            *args, **kwargs,
            )

    saw = []

    for item in e:
        general_logger.debug("run_code saw: %s",
                item)

        saw.append(item)

        state.mode.handle(
                item=item,
                tokens=e,
                )

    result = {
            'saw': saw,
            'list': state.mode.list,
            }

    general_logger.debug("run_code results: %s",
            result)

    if find is not None:
        if find in result:
            result = result[find]
        elif find=='chars':
            result = ''.join([
                x.ch for x in result['saw']
                if isinstance(x, mex.parse.Token)
                and not isinstance(x, mex.parse.Control)
                ])
        elif find=='tokens':
            result = ''.join([
                x.ch for x in result['saw']
                if isinstance(x, mex.parse.Token)
                ])
        elif find=='ch':
            result = ''.join([
                x.ch for x in result['saw']
                ])
        else:
            raise ValueError(f"Unknown value of 'find': {find}")

        if strip:
            try:
                result = result.strip()
            except:
                pass

    return result

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
            ).rstrip(' ')

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
        'run_code',
        'expand',
        'call_macro',
        'get_number',
        'get_dimen',
        'get_glue',
        'get_muglue',
        'compare_strings_with_reals',
        'expander_on_string',
        ]
