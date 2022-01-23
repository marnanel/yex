import datetime
from mex.state import State

def test_simple_create():
    s = State()
    assert s is not None

def test_read_initial():
    s = State()
    for f, expected in [
        ('count0', 0),
        ('dimen0', 0),
        ('skip0', 0),
        ('muskip0', 0),
        ]:
        assert s[f]==expected

def test_set_single():
    s = State()

    for f, newvalue in [
        ('count0', 100),
        ]:
        s[f]=newvalue

    for f, expected in [
        ('count0', 100),
        ('dimen0', 0),
        ('skip0', 0),
        ('muskip0', 0),
        ]:
        assert s[f]==expected

def test_grouping(): 
    s = State()

    for f, newvalue in [
        ('count0', 100),
        ]:
        s[f]=newvalue

    for f, expected in [
        ('count0', 100),
        ('dimen0', 0),
        ('skip0', 0),
        ('muskip0', 0),
        ]:
        assert s[f]==expected

    s.begin_group()

    for f, expected in [
        ('count0', 100),
        ('dimen0', 0),
        ('skip0', 0),
        ('muskip0', 0),
        ]:
        assert s[f]==expected

    for f, newvalue in [
        ('count0', 200),
        ]:
        s[f]=newvalue

    for f, expected in [
        ('count0', 200),
        ('dimen0', 0),
        ('skip0', 0),
        ('muskip0', 0),
        ]:
        assert s[f]==expected

    s.end_group()

    for f, expected in [
        ('count0', 100),
        ('dimen0', 0),
        ('skip0', 0),
        ('muskip0', 0),
        ]:
        assert s[f]==expected

def test_time():
    now = datetime.datetime.now()
    s = State()

    assert s['time'] == now.hour*60+now.minute
    assert s['day'] == now.day
    assert s['month'] == now.month
    assert s['year'] == now.year

def test_set_global():
    s = State()

    assert s['count0']==0

    s['count0'] = 1
    assert s['count0']==1

    s.begin_group()
    s['count0'] = 2
    assert s['count0']==2

    s.end_group()
    assert s['count0']==1

    s.begin_group()
    s.__setitem__(field='count0', value=2, use_global=True)
    assert s['count0']==2

    s.end_group()
    assert s['count0']==2
