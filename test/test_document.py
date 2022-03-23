import datetime
from yex.document import Document
import yex.output

def test_simple_create():
    doc = Document()
    assert doc is not None

def test_read_initial():
    doc = Document()
    assert doc['count0'].value==0

def test_set_single():
    doc = Document()

    assert doc['count0'].value==0
    doc['count0'].value=100
    assert doc['count0'].value==100

def test_grouping():
    doc = Document()

    doc['count0'].value=100
    assert doc['count0'].value==100

    doc.begin_group()

    doc['count0'].value=100
    doc['count1'].value=0

    doc['count0'].value=200

    doc['count0'].value=200
    doc['count1'].value=0

    doc.end_group()

    doc['count0'].value=100
    doc['count1'].value=0

def test_time():
    now = datetime.datetime.now()
    doc = Document()

    TRIES = 3

    # In case the clock has ticked forward during running the test

    for seconds in range(TRIES+1):
        when = now - datetime.timedelta(seconds=seconds)

        try:
            assert doc['time'].value == when.hour*60+when.minute
            assert doc['day'].value == when.day
            assert doc['month'].value == when.month
            assert doc['year'].value == when.year
        except AssertionError:
            if seconds==TRIES:
                raise
            else:
                continue

def test_set_global():
    doc = Document()

    assert doc['count0'].value==0

    doc['count0'].value = 1
    assert doc['count0'].value==1

    doc.begin_group()
    doc['count0'].value = 2
    assert doc['count0'].value==2

    doc.end_group()
    assert doc['count0'].value==1

    doc.begin_group()
    doc.next_assignment_is_global = True
    doc['count0'].value = 2
    assert doc['count0'].value==2

    doc.end_group()
    assert doc['count0'].value==2

def test_len():
    doc = Document()

    assert len(doc)==1

    doc.begin_group()

    assert len(doc)==2

    doc.end_group()

    assert len(doc)==1
