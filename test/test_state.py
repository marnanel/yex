import datetime
from mex.state import State

def test_simple_create():
    s = State()
    assert s is not None

def test_read_initial():
    s = State()
    assert s['count0'].value==0

def test_set_single():
    s = State()

    assert s['count0'].value==0
    s['count0']=100
    assert s['count0'].value==100

def test_grouping(): 
    s = State()

    s['count0']=100
    assert s['count0'].value==100

    s.begin_group()

    s['count0']=100
    s['count1']=0

    s['count0']=200

    s['count0']=200
    s['count1']=0

    s.end_group()

    s['count0']=100
    s['count1']=0

def test_time():
    now = datetime.datetime.now()
    s = State()

    assert s['time'].value == now.hour*60+now.minute
    assert s['day'].value == now.day
    assert s['month'].value == now.month
    assert s['year'].value == now.year

def test_set_global():
    s = State()

    assert s['count0'].value==0

    s['count0'] = 1
    assert s['count0'].value==1

    s.begin_group()
    s['count0'] = 2
    assert s['count0'].value==2

    s.end_group()
    assert s['count0'].value==1

    s.begin_group()
    s.next_assignment_is_global = True
    s['count0'] = 2
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
