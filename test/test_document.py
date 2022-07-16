import datetime
from yex.document import Document
import yex.output
from test import *
import os.path
import yex.control.parameter
import pytest
import os
import pickle

def test_simple_create():
    doc = Document()
    assert doc is not None

def test_read_initial():
    doc = Document()
    assert doc[r'\count0'].value==0

def test_set_single():
    doc = Document()

    assert doc[r'\count0'].value==0
    doc[r'\count0'].value=100
    assert doc[r'\count0'].value==100

def test_grouping():
    doc = Document()

    doc[r'\count0'].value=100
    assert doc[r'\count0'].value==100

    doc.begin_group()

    doc[r'\count0'].value=100
    doc[r'\count1'].value=0

    doc[r'\count0'].value=200

    doc[r'\count0'].value=200
    doc[r'\count1'].value=0

    doc.end_group()

    doc[r'\count0'].value=100
    doc[r'\count1'].value=0

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

def test_group_matching():
    doc = Document()

    g1 = doc.begin_group()
    assert g1 is not None
    g2 = doc.begin_group()
    assert g2 is not None
    doc.end_group(group=g2)
    doc.end_group(group=g1)

    g1 = doc.begin_group()
    g2 = doc.begin_group()
    doc.end_group()
    doc.end_group(group=g1)

    g1 = doc.begin_group()
    g2 = doc.begin_group()
    doc.end_group(group=g2)
    doc.end_group()

    g1 = doc.begin_group()
    g2 = doc.begin_group()
    doc.end_group()
    doc.end_group()

    g1 = doc.begin_group()
    g2 = doc.begin_group()
    with pytest.raises(ValueError):
        doc.end_group(group=g1)

def test_group_ephemeral():

    doc = Document()
    g1 = doc.begin_group()
    g2 = doc.begin_group()
    with pytest.raises(ValueError):
        doc.end_group(group=g1)

    doc = Document()
    g1 = doc.begin_group()
    g2 = doc.begin_group(ephemeral=True)
    doc.end_group(group=g1)

this_file_load_time = datetime.datetime.now()

def test_time():
    doc = Document()

    when = yex.control.parameter.file_load_time

    assert doc[r'\time'].value == when.hour*60+when.minute
    assert doc[r'\day'].value == when.day
    assert doc[r'\month'].value == when.month
    assert doc[r'\year'].value == when.year

    # In case the clock has ticked forward during running the test
    assert this_file_load_time-when < datetime.timedelta(seconds=3), \
        f"{when} {this_file_load_time}"

def test_set_global():
    doc = Document()

    assert doc[r'\count0'].value==0

    doc[r'\count0'].value = 1
    assert doc[r'\count0'].value==1

    doc.begin_group()
    doc[r'\count0'].value = 2
    assert doc[r'\count0'].value==2

    doc.end_group()
    assert doc[r'\count0'].value==1

    doc.begin_group()
    doc.next_assignment_is_global = True
    doc[r'\count0'].value = 2
    assert doc[r'\count0'].value==2

    doc.end_group()
    assert doc[r'\count0'].value==2

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
    y['_output'] = yex.output.get_driver_for(y, FILENAME)
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
        expected[r'_mode'] = 'vertical'
        expected[r'_full'] = False

        del found['_created']

        assert found==expected

    _serialisation_test(run)

def test_document_pickle():

    def run(
            setup,
            expected,
            ):

        original_doc = yex.Document()
        run_code(setup, doc=original_doc)

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

def test_document_end_all_groups(fs):

    doc = yex.Document()

    for i in range(10):
        assert len(doc.groups)==i
        doc.begin_group()

    doc.end_all_groups()
    assert len(doc.groups)==0

def test_document_save_ends_all_groups(yex_test_fs):

    FILENAME = "x.svg"

    doc = yex.Document()

    run_code(
            r"\hbox{X}",
            mode = None,
            doc = doc,
            )

    doc['_output'] = yex.output.get_driver_for(doc, FILENAME)
    doc.save()

    assert os.access(FILENAME, os.F_OK), "it didn't save"
    assert check_svg(FILENAME)==['X']
