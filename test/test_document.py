import datetime
from yex.document import Document
import yex.output
from test import *

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

def test_time():
    now = datetime.datetime.now()
    doc = Document()

    TRIES = 3

    # In case the clock has ticked forward during running the test

    for seconds in range(TRIES+1):
        when = now - datetime.timedelta(seconds=seconds)

        try:
            assert doc[r'\time'].value == when.hour*60+when.minute
            assert doc[r'\day'].value == when.day
            assert doc[r'\month'].value == when.month
            assert doc[r'\year'].value == when.year
        except AssertionError:
            if seconds==TRIES:
                raise
            else:
                continue

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

def test_document_save(fs):
    for filename in [
            'cmr10.tfm',
            'cmr10.pk',
            ]:
        fs.add_real_file(filename)

    message = "Lorum ipsum dolor sit amet."

    y = yex.Document()
    y += (
        r"\def\TeX{T\kern-.1667em\lower.5ex\hbox{E}\kern-.125emX}"
        r"\shipout\hbox{"
        f"{message}"
        r"}"
        )
    y.save('lorum.svg')
    result = ''.join(check_svg('lorum.svg'))

    assert result == message.replace(' ','')

def _test_font_control(
        string,
        s = None,
        ):

    if s is None:
        doc = Document()

    return doc['_font']
