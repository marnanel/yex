import io
import copy
import yex.parse
import yex.document
import yex.value
import logging
import contextlib

general_logger = logging.getLogger('yex.general')

def run_code(
        call,
        setup = None,
        doc = None,
        mode = 'vertical',
        find = None,
        strip = True,
        *args, **kwargs,
        ):
    r"""
    Instruments and runs some code, and returns details.

    Parameters:

        call -      TeX code to run
        setup -     TeX code to run before running "call",
                    or None to run nothing. This code is
                    run on the same Document, but isn't used
                    for testing.
        doc -     the Document to run the code on. If None,
                    we create a new Document just for this test.
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
    if doc is None:
        doc = yex.document.Document()

    if mode=='dummy':
        class DummyMode:
            def __init__(self, doc):
                self.doc = doc
                self.name = 'dummy'
                self.list = []

            def handle(self, item, tokens):
                general_logger.debug("dummy mode saw: %s",
                        item)

        doc.mode_handlers[mode] = DummyMode

    doc['_mode'] = mode

    if 'on_eof' not in kwargs:
        kwargs['on_eof'] = yex.parse.Expander.EOF_EXHAUST

    if setup is not None:
        general_logger.debug("=== run_code sets up: %s ===",
                setup)

        tokens = doc.open(setup, **kwargs)

        for item in tokens:
            if isinstance(item, yex.parse.Token) and \
                    item.category==item.INTERNAL:
                continue

            doc.mode.handle(
                    item = item,
                    tokens = tokens,
                    )

    general_logger.debug("=== run_code begins: %s ===",
            call)

    saw = []

    tokens = doc.open(call, **kwargs)

    for item in tokens:
        general_logger.debug("run_code saw: %s",
                item)

        if isinstance(item, yex.parse.Token) and item.category==item.INTERNAL:
            continue

        saw.append(item)

        doc.mode.handle(
                item=item,
                tokens=tokens,
                )

    result = {
            'saw': saw,
            'list': doc.mode.list,
            }

    general_logger.debug("run_code results: %s",
            result)

    if find is not None:
        if find in result:
            result = result[find]
        elif find=='chars':
            result = ''.join([
                x.ch for x in result['saw']
                if isinstance(x, yex.parse.Token)
                and not isinstance(x, yex.parse.Control)
                ])
        elif find=='tokens':
            result = ''.join([
                x.ch for x in result['saw']
                if isinstance(x, yex.parse.Token)
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

def tokenise_and_get(string, cls, doc = None):
    """
    Creates a Document, opens an Expander with the string "string",
    and initialises the class "cls" with that Expander.

    The string should represent the new value followed
    by the letter "q" (so we can test how well literals are
    delimited by the following characters).

    If you pass in "doc", uses that Document instead of
    constructing a new one.

    Returns the result.
    """

    if doc is None:
        doc = yex.document.Document()

    with expander_on_string(string, doc,
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
        doc = None,
        raw = False,
        ):
    """
    See tokenise_and_get().
    """

    result = tokenise_and_get(string,
            cls=yex.value.Number,
            doc=doc,
            )

    if raw:
        return result

    return result.value

def get_dimen(string,
        doc = None,
        ):
    """
    See tokenise_and_get().
    """

    result = tokenise_and_get(string,
            cls=yex.value.Dimen,
            doc=doc,
            )

    return result

def get_glue(string,
        doc = None,
        raw = False):
    """
    See tokenise_and_get().

    If raw is True, returns the Glue object;
    otherwise returns a tuple:
       (space, stretch, shrink, stretch_infinity,
       shrink_infinity).
    """

    result = tokenise_and_get(string,
            cls=yex.value.Glue,
            doc=doc)

    if raw:
        return result

    return (
            float(result.space),
            float(result.stretch),
            float(result.shrink),
            result.stretch.infinity,
            result.shrink.infinity,
            )

def get_muglue(string,
        doc = None,
        raw = False):
    """
    See tokenise_and_get().

    If raw is True, returns the Muglue object;
    otherwise returns a tuple:
       (space, stretch, shrink, stretch_infinity,
       shrink_infinity).
    """

    result = tokenise_and_get(string,
            cls=yex.value.Muglue,
            doc=doc)

    if raw:
        return result

    return (
            result.space.value,
            result.stretch.value,
            result.shrink.value,
            result.stretch.infinity,
            result.shrink.infinity,
            )

def get_boxes(string,
        doc = None):

    # Can't use tokenise_and_get here because a Box can't be
    # constructed literally

    if doc is None:
        doc = yex.document.Document()

    saw = run_code(string,
            mode='dummy',
            find='saw',
            )

    result = [x for x in saw if isinstance(x, yex.box.Box)]
    general_logger.info("get_boxes found: %s",
            result)

    return result

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
def expander_on_string(string, doc=None,
         **kwargs):

    if doc is None:
        doc = yex.document.Document()

    yield doc.open(string, **kwargs)

def compare_copy_and_deepcopy(thing):
    """
    Compares thing, copy(thing), and deepcopy(thing), by assertion.
    They must all be equal and have the same type.

    Deepcopy must result in different objects; copy may or may not.

    Returns None.
    """

    print(type(thing))
    a = {0:thing} # ensure a compound type

    a_c = copy.copy(a)

    assert a[0]==a_c[0], f"{thing}'s copy was not equal"
    assert type(a[0])==type(a_c[0]), f"{thing}'s copy was a different type"
    assert type(thing)==type(a[0])
    assert type(thing)==type(a_c[0])

    a_dc = copy.deepcopy(a)

    print(a, a_dc)

    assert a[0] is not a_dc[0], f"{thing} did not deepcopy"
    assert a[0]==a_dc[0], f"{thing}'s deepcopy was not equal"
    assert type(a[0])==type(a_dc[0]), (
        f"{thing}'s deepcopy was a different type")
    assert type(thing)==type(a[0]) # again
    assert type(thing)==type(a_dc[0])

__all__ = [
        'run_code',
        'get_number',
        'get_dimen',
        'get_glue',
        'get_muglue',
        'get_boxes',
        'compare_strings_with_reals',
        'expander_on_string',
        'compare_copy_and_deepcopy',
        ]
