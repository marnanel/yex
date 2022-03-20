import datetime
from yex.state import State
import yex.output

def test_simple_create():
    s = State()
    assert s is not None

def test_read_initial():
    s = State()
    assert s['count0'].value==0

def test_set_single():
    s = State()

    assert s['count0'].value==0
    s['count0'].value=100
    assert s['count0'].value==100

def test_grouping(): 
    s = State()

    s['count0'].value=100
    assert s['count0'].value==100

    s.begin_group()

    s['count0'].value=100
    s['count1'].value=0

    s['count0'].value=200

    s['count0'].value=200
    s['count1'].value=0

    s.end_group()

    s['count0'].value=100
    s['count1'].value=0

def test_time():
    now = datetime.datetime.now()
    s = State()

    TRIES = 3

    # In case the clock has ticked forward during running the test

    for seconds in range(TRIES+1):
        when = now - datetime.timedelta(seconds=seconds)

        try:
            assert s['time'].value == when.hour*60+when.minute
            assert s['day'].value == when.day
            assert s['month'].value == when.month
            assert s['year'].value == when.year
        except AssertionError:
            if seconds==TRIES:
                raise
            else:
                continue

def test_set_global():
    s = State()

    assert s['count0'].value==0

    s['count0'].value = 1
    assert s['count0'].value==1

    s.begin_group()
    s['count0'].value = 2
    assert s['count0'].value==2

    s.end_group()
    assert s['count0'].value==1

    s.begin_group()
    s.next_assignment_is_global = True
    s['count0'].value = 2
    assert s['count0'].value==2

    s.end_group()
    assert s['count0'].value==2

def test_len():
    s = State()

    assert len(s)==1

    s.begin_group()

    assert len(s)==2

    s.end_group()

    assert len(s)==1

def test_state_output():
    s = State()
    assert(isinstance(s['_output'], yex.output.Output))
