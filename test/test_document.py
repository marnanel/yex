import datetime
from yex.document import Document
import yex.output
from test import *
import os.path
import yex.control.parameter
import pytest
import os

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

def test_document_len():
    doc = Document()

    assert len(doc)==1

    doc.begin_group()

    assert len(doc)==2

    doc.end_group()

    assert len(doc)==1

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
    driver = yex.output.get_driver_for(y, FILENAME)
    y.save(FILENAME, driver=driver)

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
            doc = doc,
            )

    driver = yex.output.get_driver_for(doc, FILENAME)
    doc.save(FILENAME, driver=driver)

    assert os.access(FILENAME, os.F_OK), "it didn't save"
    assert check_svg(FILENAME)==['X']
