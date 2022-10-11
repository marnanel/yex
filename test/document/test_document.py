import datetime
from yex.document import Document
import yex.output
from test import *
import os.path
import yex.control.parameter
import pytest
import os
import pickle

def test_document_simple_create():
    doc = Document()
    assert doc is not None

def test_document_read_initial():
    doc = Document()
    assert doc[r'\count0']==0

def test_document_set_single():
    doc = Document()

    assert doc[r'\count0']==0
    doc[r'\count0']=100
    assert doc[r'\count0']==100

def test_document_catcode():

    def do_checks(doc, circumflex, underscore):
        assert doc.registers['catcode']['^']==circumflex
        assert doc.registers['catcode']['_']==underscore
        assert doc['catcode;94']==circumflex
        assert doc['catcode;95']==underscore

    doc = Document()
    do_checks(doc, 7, 8)

    doc['catcode;94']=10
    do_checks(doc, 10, 8)

this_file_load_time = datetime.datetime.now()

def test_document_time():
    doc = Document()

    when = yex.control.parameter.file_load_time

    assert doc[r'\time'] == when.hour*60+when.minute
    assert doc[r'\day'] == when.day
    assert doc[r'\month'] == when.month
    assert doc[r'\year'] == when.year

    # In case the clock has ticked forward during running the test
    assert this_file_load_time-when < datetime.timedelta(seconds=3), \
        f"{when} {this_file_load_time}"

def test_document_save(yex_test_fs):

    message = "Lorum ipsum dolor sit amet."

    y = yex.Document()
    y += (
        r"\def\TeX{T\kern-.1667em\lower.5ex\hbox{E}\kern-.125emX}"
        r"\shipout\hbox{"
        f"{message}"
        r"}"
        )

    FILENAME = 'lorum.svg'
    y['_output'] = yex.output.Output.driver_for(y, FILENAME)
    y.save()

    result = ''.join(check_svg(FILENAME))

    assert result == message.replace(' ','')

def _test_font_control(
        string,
        s = None,
        ):

    if s is None:
        doc = Document()

    return doc['_font']

def test_control_symbols():
    s = yex.document.Document()

    # Let's look up three controls which are all horizontal unexpandables:

    for name in [
            # an example of a control token:
            r'\discretionary',

            # two examples of control symbols:
            r'\-',
            r'\ ',
            ]:
        handler = s[name]
        assert handler.horizontal, f"{name} is a valid horizontal control"

def _normalise_value(v):
    if hasattr(v, 'value'):
        # dereference register
        v = v.value

    if hasattr(v, '__getstate__'):
        # normalise type
        v = v.__getstate__()

    return v

def test_document_serialisation_by_lookup():

    # This doesn't actually test serialisation directly;
    # it just checks that the doc[...] values are as expected
    # after running the setup, even when we're not serialising.

    def run(
            setup,
            expected,
            ):

        doc = yex.Document()
        run_code(setup, doc=doc)

        for f, v in expected.items():
            found = _normalise_value(doc[f])

            assert found==v, setup

    _serialisation_test(run)

def test_document_getstate():

    def run(
            setup,
            expected,
            ):

        doc = yex.Document()
        run_code(setup,
                mode='vertical',
                doc=doc)

        found = doc.__getstate__(
                full = False,
                )

        expected[r'_format'] = 1
        expected[r'_full'] = False

        del found['_created']

        assert found==expected

    _serialisation_test(run)

@pytest.mark.xfail
def test_document_pickle():

    def run(
            setup,
            expected,
            ):

        original_doc = yex.Document()
        run_code(
                setup,
                mode='vertical',
                output='none',
                doc=original_doc,
                )

        for f, v in expected.items():
            found = _normalise_value(original_doc[f])

            assert found==v, f"original doc -- {setup}"

        doc_pickle = pickle.dumps(original_doc)

        new_doc = pickle.loads(doc_pickle)

        assert new_doc is not original_doc

        for f, v in expected.items():
            found = _normalise_value(new_doc[f])

            assert found==v, f"new doc -- {setup}"

    _serialisation_test(run)

def _serialisation_test(run):
    run(
            setup = r'\count23=12',
            expected = {
                r'\count23': 12,
                },
            )

    run(
            setup = r'\dimen23=23pt',
            expected = {
                r'\dimen23': 23*65536,
                },
            )

    run(
            setup = (
                r'\skip23=23pt '
                r'\skip24=23pt plus 50pt '
                r'\skip25=23pt plus 50pt minus 70pt'
                ),
            expected = {
                r'\skip23': [ 23*65536, ],
                r'\skip24': [ 23*65536, 50*65536, 0, ],
                r'\skip25': [ 23*65536, 50*65536, 0, 70*65536, 0],
                },
            )

    # FIXME muskip

    MESSAGE = 'I have 12 wombats'
    run(
            setup = (
                r'\toks23={'+\
                MESSAGE+\
                '}'
                ),
            expected = {
                r'\toks23': MESSAGE,
                },
            )

    run(
            setup = (
                r'\def\thing a#1b#2c{123#1}'
                ),
            expected = {
                r'\thing': {
                    'macro': 'thing',
                    'definition': '123#1',
                    'parameters': ['a', 'b', 'c'],
                    'starts_at': '<str>:1:20',
                    },
                },
            )

def _swallow(doc):
    result = ''

    for t in source:
        if t is None:
            break
        result += str(t)

    return result.rstrip('\r')

def test_document_pushback_full():

    def run(pushed, source, expected):

        doc = yex.Document()
        t = yex.parse.Tokeniser(
                doc = doc,
                source = source,
                )
        e = yex.parse.Expander(
                t,
                on_eof='exhaust',
                )

        doc.pushback.push(pushed)
        doc.end_all_groups()
        found = ''.join([item.ch for item in e]).rstrip()
        assert found==expected, f"pushed={pushed}, source={source}"

    run('b', 'ovine', 'bovine')
    run('secret', 'arial', 'secretarial')
    run(None, 'wombat', 'wombat')
    run([chr(x) for x in range(ord('n'), ord('q'))],
            'roblem',
            'noproblem')

def test_document_pushback_partway(fs):
    doc = yex.Document()
    t = yex.parse.Tokeniser(
            doc = doc,
            source = 'dogs',
            )
    e = yex.parse.Expander(
            t,
            on_eof='exhaust',
            )
    i = iter(e)

    def get():
        try:
            return next(i).ch
        except StopIteration:
            return None

    assert get()=='d'
    assert get()=='o'
    doc.pushback.push('i')
    assert get()=='i'
    assert get()=='g'
    doc.pushback.push('t')
    doc.pushback.push('a')
    doc.pushback.push('c')
    assert get()=='c'
    assert get()=='a'
    assert get()=='t'
    assert get()=='s'
    assert get()==' '
    assert get() is None
