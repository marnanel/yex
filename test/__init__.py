import io
import copy
import yex
import logging
import contextlib
import pytest
import os
import importlib

logger = logging.getLogger('yex.general')

def run_code(
        call,
        setup = None,
        doc = None,
        mode = None,
        output = 'dummy',
        find = None,
        strip = True,
        on_each = None,
        auto_save = True,
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
        doc -       the Document to run the code on. If None,
                    we create a new Document just for this test.
        mode -      the mode to start in. Defaults to "vertical".
                    Pass in `None` to leave the mode where it is.
                    If you set this to "dummy", we splice in
                    a dummy Mode which does nothing. This lets
                    you test code which would annoy all the real modes.
        output -    the output driver to use. As with "mode",
                    you can set this to "dummy" to get a dummy Output.
                    This is also the default.
        strip -     if True, and the result would be a string,
                    run strip() on it before returning.
                    (Sometimes the phantom EOL at the end of a string
                    causes a Mode to insert a space.)
                    If this fails, we continue silently.
                    Defaults to True.
        on_each -   callable which gets called each time the Expander
                    sends something to the Mode, with two arguments:
                    the expander and the item that was sent.
                    A list of its return values is in the return result:
                    see below.
                    `on_each` functions can see Internal tokens, which
                    are otherwise ignored by this routine.
                    Defaults to None, in which case nothing gets called.
        find -      affects the results you get; see below.
        auto_save - if True, which is the default, we save the document
                    after the call. If False, the document is left
                    unsaved; if the code ends partway through a group,
                    it's an error for auto_save to be False.

        If find is not None, it should be a string, or a list or tuple
        of strings. If it's a string, we return a result according to the
        following table. If it's a list or tuple, we return a dict mapping
        those strings to results found in a similar way.

        If find is None, which is the default, it behaves as though you
        had specified ['saw', 'saw_all', 'list'], and also 'returns'
        if on_each was set.

        Other things find can be:

        saw -       a list of everything which the Expander sent to
                    the Mode. run_code() sits between the two and
                    records it all.
        saw_all -   a list of everything which the Expander returned.
                    run_code() sits between the two and records it all.
        list -      the "list" attribute of the outermost Mode
                    after the test code finished.
        returns -   only if `on_each` is not `None`: the return values
                    of each call to `on_each`.
        chars -     returns a string, the names of the non-control
                    Tokens in 'saw'. For example, a letter token for "B"
                    adds a "B" to the string.
        tokens -    like 'chars', except control Tokens are included.
                    Control tokens add their name to the string,
                    like "\kern".
        ch -        like 'chars', except everything is included.
                    Whatever the item's 'ch' method returns gets added.
        chars_all - Like chars, but using "saw_all" rather than "saw".
        tokens_all -Like tokens, but using "saw_all" rather than "saw".
        ch_all -    Like ch, but using "saw_all" rather than "saw".
        chars_list- Like chars, but using the list of the outermost mode
        tokens_list Like tokens, but using the list of the outermost mode
        hboxes -    All \hbox{}s which have been sent to the output driver.
                    Requires output='dummy'. This automatically saves the
                    document, so you won't be able to use that document
                    for anything else afterwards.
        items -     like "hboxes" except that all HBoxes and VBoxes are
                    expanded.
        tex -       instead of running anything, TeX will be invoked as if
                    "YEX_TEST_WITH_TEX" had been set. If a DVI is produced,
                    we then run it through dvi2tty, strip the result and
                    return it. If not, we raise an Exception with
                    the contents of the logfile as its message.
                    For quick and dirty testing when debugging.
                    Don't use this in production, please! It WILL fail in CI.
        expander -  the Expander we used for the call (not the setup).

        Some of these options have unhelpful names.

        For historical reasons, "chars" and "tokens" consider Paragraph
        tokens to be controls, even though they're not.

        If you set the environment variable "YEX_TEST_WITH_TEX" to 1,
        everything run through here will also be saved to a file
        whose name is based on the test name. "\end" will be added
        automatically to such a file if it's not already there.
        TeX will then be run on that file. Multiple invocations of
        run_code() in the same test will result in files with successive
        numbers at the end of the filename. Whatever happens when TeX is
        invoked doesn't matter to the test: it will go on regardless.
        If you do this with the full test suite, be prepared to
        tidy up your directory afterwards.
    """
    if find=='tex':
        result = _run_tex_on(setup, call)
        logger.debug("run_code: TeX returns: %s", result)
        return result

    elif os.environ.get('YEX_TEST_WITH_TEX'):
        _run_tex_on(setup, call, ignore_result=True)

    if doc is None:
        doc = yex.document.Document()

    if mode=='dummy':
        class DummyMode:

            is_inner = False
            name = 'dummy'

            def __init__(self, doc):
                self.doc = doc
                self.filename = 'dummy'
                self.list = []

            def exercise_page_builder(self):
                logger.debug("dummy mode: exercise page builder (a no-op)")

            def handle(self, item, tokens):
                if isinstance(item, yex.parse.BeginningGroup):
                    logger.debug("dummy mode: beginning a group")
                    self.doc.begin_group()

                elif isinstance(item, yex.parse.EndGroup):
                    logger.debug("dummy mode: ending a group")
                    self.doc.end_group(tokens=tokens)
                else:
                    logger.debug("dummy mode saw: %s",
                            item)

            def append(self, item):
                logger.debug("dummy mode received: %s",
                        item)
                self.list.append(item)

            def run_single(self, tokens):
                logger.debug("dummy mode: run_single begins")

                tokens = tokens.another(
                        on_eof='exhaust',
                        level='executing',
                        bounded='single',
                        )

                for token in tokens:
                    self.handle(token, tokens)

                logger.debug("dummy mode: run_single ends")

                return self.list

            def result(self):
                return self.list

            def close(self):
                logger.debug("dummy mode: closed")

            def __getstate__(self):
                return 'dummy'

        yex.mode.Mode.handlers[mode] = DummyMode

    if output=='dummy':
        class DummyOutputDriver(yex.output.Output):
            def __init__(self):
                self.found = None
            def render(self):
                self.found = doc.contents
                logger.debug("output driver called with: %s", self.found)
            def __getstate__(self):
                return 'dummy'
            def hboxes(self):
                if not self.found:
                    result = []
                else:
                    result = [box for box in
                            self.found[0]
                            if isinstance(box, yex.box.HBox)]
                return result

        doc['_output'] = DummyOutputDriver()
    else:
        doc['_output'] = output

    if mode is not None:
        doc['_mode'] = mode
        doc.outermost_mode = doc['_mode']

    if 'on_eof' not in kwargs:
        kwargs['on_eof'] = "exhaust"

    if setup is not None:
        logger.debug("=== run_code sets up: %s ===",
                setup)

        tokens = doc.open(setup, **kwargs)

        for item in tokens:
            if isinstance(item, yex.parse.Internal):
                continue

            doc.mode.handle(
                    item = item,
                    tokens = tokens,
                    )

    logger.debug("=== run_code begins: %s ===",
            call)

    saw = []
    saw_all = []
    on_each_returns = []

    tokens = doc.open(call, **kwargs)

    for item in tokens:
        logger.debug("run_code: saw: %s",
                item)

        if on_each:
            logger.debug("run_code: calling %s",
                    on_each)

            received = on_each(tokens, item)

            logger.debug("run_code: %s gave us %s",
                    on_each, received)

            on_each_returns.append(received)

        if isinstance(item, yex.parse.Internal):
            continue

        saw_all.append(item)
        if doc.mode!=doc.outermost_mode:
            saw.append(item)

        doc.mode.handle(
                item=item,
                tokens=tokens,
                )

    if auto_save:
        if doc.groups:
            raise ValueError(
                    "auto_save was set, but we ended partway through a group; "
                    "for safety, you must set auto_save=False and call "
                    "doc.save yourself."
                    )
        doc.save()

    found = {
            'saw': saw,
            'saw_all': saw_all,
            'list': doc.contents,
            }

    if on_each is not None:
        found['returns'] = on_each_returns

    logger.debug("run_code results: %s",
            found)

    def get_ch(x):
        if isinstance(x, list):
            return ''.join([get_ch(item) for item in x])

        try:
            return x.ch
        except AttributeError:
            try:
                return x.identifier
            except AttributeError:
                return str(x)

    def atomic_items(item=None):

        if item is None:
            item = found['list']

        result = []
        if isinstance(item, (list, yex.box.HVBox)):
            for thing in item:
                result.extend(atomic_items(thing))
        else:
            result.append(item)

        return result

    def finding(what):

        source = 'saw'
        if what!='saw_all' and what.endswith('_all'):
            what = what[:-4]
            source = 'saw_all'
        elif what.endswith('_list'):
            what = what[:-5]
            source = 'list'

        if what in found:
            return found[what]
        elif what=='chars':
            return ''.join([
                get_ch(x) for x in found[source]
                if isinstance(x, yex.parse.Token)
                and not isinstance(x, (
                    yex.parse.Control,
                    yex.parse.Active,
                    yex.parse.Paragraph,
                    ))])
        elif what=='tokens':
            return ''.join([
                get_ch(x) for x in found[source]
                if isinstance(x, yex.parse.Token)
                and not isinstance(x, yex.parse.Paragraph)
                ])
        elif what=='items':
            return atomic_items()
        elif what=='ch':
            return ''.join([
                get_ch(x) for x in found[source]
                ])
        elif what=='hboxes':
            assert output=='dummy'
            return doc.output.hboxes()
        elif what=='expander':
            return tokens
        else:
            raise ValueError(f"Unknown value of 'find': {what}")

    def maybe_strip(n):
        if not strip:
            return n

        try:
            if isinstance(n, list) and n:
                while isinstance(n[-1], yex.parse.Space):
                    n = n[:-1]
                return n
            else:
                return n.strip()
        except:
            return n

    if find is None:
        result = found
    elif isinstance(find, (list, tuple)):
        result = dict([(thing, maybe_strip(finding(thing)))
            for thing in find])

    else:
        result = maybe_strip(finding(find))

    if auto_save:
        doc.contents = []

    logger.debug("run_code returns: %s",
            result)

    return result

_last_tex_run_filename = (None, 0)

def _run_tex_on(setup, call,
        ignore_result = False,
        ):
    import subprocess
    global _last_tex_run_filename

    basename = os.environ.get(
            'PYTEST_CURRENT_TEST').split(':')[-1].split(' ')[0]

    if _last_tex_run_filename[0]==basename:
        _last_tex_run_filename = (
                basename,
                _last_tex_run_filename[1]+1,
                )
    else:
        _last_tex_run_filename = (
                basename,
                1,
                )

    basename = f"{basename}-{_last_tex_run_filename[1]}"

    for extension in ['dvi', 'log']:
        try:
            os.unlink(f'{basename}.{extension}')
        except FileNotFoundError:
            pass

    setup = setup or ''

    string = f"{setup}\n{call}"
    if not string.endswith(r'\end'):
        string += r'\end'

    with open(basename+'.tex', 'w') as out:
        out.write(string)

    subprocess.call([
            '/usr/bin/tex',
            '-interaction=nonstopmode',
            f'{basename}.tex',
            ])

    if ignore_result:
        return

    if not os.path.exists(f'{basename}.dvi'):
        with open(f'{basename}.log', 'r') as log:
            raise Exception(log.read())

    result = subprocess.check_output([
        '/usr/bin/dvi2tty',
        f'{basename}.dvi',
        ]).decode('ascii').strip()

    if result.endswith('1'): # page number
        result = result[:-1].strip()

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
            level='reading') as e:

        result = cls.from_tokens(e)

        while True:
            q = e.next()

            if q is None:
                raise ValueError("Wanted trailing 'q' for "
                        f'"{string}" but found nothing')

            if isinstance(q, yex.parse.Letter) and q.ch=='q':
                return result

            elif isinstance(q, yex.parse.Space):
                pass

            else:
                raise ValueError(f"Wanted trailing 'q' for "
                        f'"{string}" but found {q}')

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
            result.space.value/65536,
            result.stretch.value/65536,
            result.shrink.value/65536,
            result.stretch.infinity,
            result.shrink.infinity,
            )

def get_boxes(string,
        doc = None):

    # Can't use tokenise_and_get here because a Box can't be
    # constructed literally
    # (see issue 20)

    if doc is None:
        doc = yex.document.Document()

    saw = run_code(string,
            mode='dummy',
            find='saw_all',
            level='executing',
            doc=doc,
            )

    result = [x for x in saw if isinstance(x, yex.box.Box)]
    logger.info("get_boxes found: %s",
            result)

    return result

def compare_strings_with_reals(
        left, right, tolerance=0.1,
        ):
    import re

    real = re.compile(r"([0-9]+(?:\.[0-9]+)?)")

    left = real.split(left)
    right = real.split(right)

    assert len(left)==len(right), (
            f"{left} and {right} have different lengths-- "
            "this may be caused by debug prints"
            )

    for l, r in zip(left, right):
        try:
            l = float(l)
            r = float(r)
            diff = abs(l-r)
        except ValueError:
            diff = None

        if diff is None:
            assert l==r, f'{l}!={r}'
        else:
            assert diff<=tolerance, (
                    f'{l}!={r} (diff={diff}, tolerance={tolerance})'
                    )

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

    a = {0:thing} # ensure a compound type

    a_c = copy.copy(a)

    assert a[0]==a_c[0], f"{thing}'s copy was not equal"
    assert type(a[0])==type(a_c[0]), f"{thing}'s copy was a different type"
    assert type(thing)==type(a[0])
    assert type(thing)==type(a_c[0])

    a_dc = copy.deepcopy(a)

    assert a[0] is not a_dc[0], f"{thing} did not deepcopy"
    assert a[0]==a_dc[0], (
            'Deepcopy for %s (of type "%s") was not equal: '
            'original.__getstate__() was %s, '
            'but respawn.__getstate__() was %s'
            ) % (
                    thing,
                    type(thing),
                    a[0].__getstate__(),
                    a_dc[0].__getstate__(),
            )
    assert type(a[0])==type(a_dc[0]), (
        f"{thing}'s deepcopy was a different type")
    assert type(thing)==type(a[0]) # again
    assert type(thing)==type(a_dc[0])

def check_svg(
        filename,
        on_char=None,
        ):
    r"""
    Load an SVG file, perform some very basic checks, and do something for
    each character.

    Args:
        filename(str): the filename of the SVG file.
        on_char(callable): what to do for each character.
            This gets called with one parameter, the element's attributes.
            If this is unspecified or None, use a default handler
            which returns the character as a string of length 1.

    Returns:
        a list of the results of the `on_char` calls.
    """

    import xml.sax

    if on_char is None:
        def just_the_char(attrs):

            PREFIX = 'charbox letter-'

            try:
                if attrs['class'].startswith(PREFIX):
                    value = attrs['class'][len(PREFIX):]
                    if len(value)==1:
                        return value
                    else:
                        return chr(int(value, 16))
            except KeyError:
                return ''

        on_char = just_the_char

    class SvgHandler(xml.sax.ContentHandler):
        EXPECTED_TAG_ORDER = [
                'svg',
                'title',
                'style',
                'g',
                ]

        def __init__(self):
            self.tag_count = -1
            self.latest_rect = None
            self.result = []

        def startElement(self, tag, attributes):
            self.tag_count += 1

            # header stuff?
            try:
                assert tag==self.EXPECTED_TAG_ORDER[self.tag_count]
                return
            except IndexError:
                pass

            if tag=='rect':
                if 'charbox' in attributes['class']:
                    assert self.latest_rect is None
                    self.latest_rect = attributes
            elif tag=='image':
                assert self.latest_rect is not None
                for name in ['width', 'height', 'x', 'y']:
                    assert self.latest_rect[name] == attributes[name]

                self.result.append(
                    on_char(attributes),
                    )

                self.latest_rect = None
            else:
                assert self.latest_rect is None

    handler = SvgHandler()
    parser = xml.sax.parse(
            filename,
            handler,
            )

    return handler.result

@pytest.fixture
def yex_test_fs(fs, filenames=None):
    """
    Sets up a fake filesystem with important fonts loaded.
    """

    if filenames is None:
        dirname = importlib.resources.files(yex) / "res" / "fonts"
        filenames = [str(dirname / f) for f in [
            'cmr10.tfm',
            'cmr10.pk',
            'cmti10.tfm',
            'cmti10.pk',
            ]]

    for filename in filenames:
        fs.add_real_file(
                source_path = filename,
                target_path = filename,
                )
        logger.debug("Copied in %s", filename)

    yield fs

def box_contents_to_string(box):
    """
    Returns a string vaguely representing the contents of a Box.

    The items are separated by spaces. WordBox and CharBox are represented
    by their contents. Other Boxes are represented recursively, surrounded
    by square brackets.

    Leaders/glue are represented by an underscore; Breakpoints by a caret;
    DiscretionaryBreaks by a hyphen.

    Everything else is run through str().

    Args:
        box (Box): the box

    Returns:
        a string representing box
    """
    def munge(item):

        if isinstance(item, (yex.box.WordBox, yex.box.CharBox)):
            return item.ch
        elif isinstance(item, yex.box.Leader):
            return '_'
        elif isinstance(item, yex.box.DiscretionaryBreak):
            return '-'
        elif isinstance(item, yex.box.Breakpoint):
            return '^'
        elif isinstance(item, yex.box.Box):
            inner = box_contents_to_string(item)
            return f'[{inner}]'
        else:
            return str(item)

    result = ' '.join([munge(item) for item in box.contents])
    return result

def construct_from_another(
        obj,
        fields):

    second = obj.__class__.from_another(obj)

    assert obj==second, f"{obj} vs {second}"
    assert id(obj)!=id(second), f"id({obj}) vs id({field})"

    for field in fields:
        obj_value = getattr(obj, field)
        second_value = getattr(second, field)

        assert obj_value==second_value, (
                    f"{field}: "
                    f"for {obj} was {obj_value}; "
                    f"for {second} was {second_value}"
                    )

        if not isinstance(obj_value,
                (int, str, float, bool, bytes)
                ):
            assert id(obj_value)!=id(second_value), (
                    f"id(.{field}): "
                    f"for {obj} was {obj_value}: {id(obj_value)}; "
                    f"for {second} was {second_value}: {id(second_value)}"
                    )

    return second

def pickle_test(
        original,
        assertions,
        ):
    r"""
    Pickle an object, unpickle it, and run some comparisons.

    We always assert that the original "is not" the respawn.

    Args:
        original: any object which can be pickled
        assertions (list of pairs of (callable, string)):
            Callables to produce pairs which should be equal.
            Each takes one argument. Each is called twice, once with
            the original as argument, and once with the respawn.
            The string is a message to display as context for errors.
    """

    import pickle
    import inspect

    pickled_original = pickle.dumps(original)

    respawn = pickle.loads(pickled_original)

    for assertion, message in assertions:

        for what, name in [
                (original, 'original'),
                (respawn, 'respawn'),
                ]:
            pair = assertion(what)

            assert pair[0]==pair[1], (
                    f"{name} of {repr(message)}: {pair[0]} != {pair[1]}"
                    )

TEX_LOGO = (
        r"\hbox{T\kern-.1667em\lower.5ex\hbox{E}\kern-.125emX}"
        )

def issue_708_workaround():
    # Workaround for https://github.com/jmcgeheeiv/pyfakefs/issues/708
    try:
        open.__self__.skip_names.remove('io')
    except KeyError:
        pass

def debug_banner(s, logger_name='yex'):
    import logging

    logger = logging.getLogger(logger_name)

    logger.debug(
            '\n\n'
            f'{"=" * 60}\n'
            '\n'
            f'{s}\n'
            '\n'
            f'{"=" * 60}\n'
            '\n'
            )

__all__ = [
        'run_code',
        'debug_banner',
        'get_number',
        'get_dimen',
        'get_glue',
        'get_muglue',
        'get_boxes',
        'compare_strings_with_reals',
        'expander_on_string',
        'compare_copy_and_deepcopy',
        'check_svg',
        'yex_test_fs',
        'box_contents_to_string',
        'construct_from_another',
        'pickle_test',
        'TEX_LOGO',
        'issue_708_workaround',
        ]
