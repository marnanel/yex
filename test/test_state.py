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
