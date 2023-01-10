import io
import pytest
import copy
from yex.document import Document
from yex.value import Number, Dimen, Glue
import yex.exception
from .. import *
import yex.put
import yex.box
import logging

logger = logging.getLogger('yex.general')

def test_glue_variable():

    VARIABLES = [
            "baselineskip",
            "lineskip",
            "parskip",
            "abovedisplayskip",
            "abovedisplayshortskip",
            "belowdisplayskip",
            "belowdisplayshortskip",
            "leftskip",
            "rightskip",
            "topskip",
            "splittopskip",
            "tabskip",
            "spaceskip",
            "xspaceskip",
            "parfillskip",

            "skip77",
            ]

    s = Document()

    for i, variable in enumerate(VARIABLES):
        s[fr'\{variable}'] = yex.value.Glue(space=Dimen(i))

    for i, variable in enumerate(VARIABLES):
        assert get_glue(
                fr"\{variable} q",s
                ) == (i, 0.0, 0.0, 0.0, 0), variable

def test_glue_literal():
    assert get_glue("2.0ptq") == (2.0, 0.0, 0.0, 0, 0)
    assert get_glue("2.0pt plus 5ptq") == (2.0, 5.0, 0.0, 0, 0)
    assert get_glue("2.0pt minus 5ptq") == (2.0, 0.0, 5.0, 0, 0)
    assert get_glue("2.0pt plus 5pt minus 5ptq") == (2.0, 5.0, 5.0, 0, 0)

def test_glue_literal_fil():
    assert get_glue("2.0pt plus 5fil minus 5fillq") == (2.0, 5.0, 5.0, 1, 2)
    assert get_glue("2.0pt plus 5filll minus 5fillq") == (2.0, 5.0, 5.0, 3, 2)

def test_glue_repr():
    def _test_repr(s):
        assert str(get_glue(f'{s}q', raw=True)) == s

    _test_repr('2.0pt plus 5.0pt')
    _test_repr('2.0pt plus 5.0fil')
    _test_repr('2.0pt plus 5.0fill')
    _test_repr('2.0pt plus 5.0filll minus 5fil')

def test_leader_construction():
    glue = yex.value.Glue(space=9, stretch=3, shrink=1)

    leader1 = yex.box.Leader(space=9, stretch=3, shrink=1)
    leader2 = yex.box.Leader(glue=glue)

    assert leader1.space   == leader2.space   == glue.space   == 9
    assert leader1.stretch == leader2.stretch == glue.stretch == 3
    assert leader1.shrink  == leader2.shrink  == glue.shrink  == 1

def test_glue_eq():
    a = get_glue('42pt plus 2pt minus 1ptq', raw=True)
    b = get_glue('42pt plus 2pt minus 1ptq', raw=True)
    c = get_glue('42pt plus 2ptq', raw=True)

    for x in [a, b, c]:
        assert isinstance(x, yex.value.Glue), x

    assert a==b
    assert a!=c
    assert b!=c

    assert a!=None
    assert not (a==None)

def test_glue_deepcopy():
    a = [Glue()]
    b = copy.copy(a)

    assert a[0] is b[0]

    c = copy.deepcopy(a)

    assert a[0] is not c[0]

def test_glue_deepcopy():
    # Constructed from literal
    compare_copy_and_deepcopy(Glue(0))

    # Constructed from tokeniser
    compare_copy_and_deepcopy(get_glue("1em plus 2ptq", raw=True))

def test_glue_from_another():
    first = yex.value.Glue(
            space=1, stretch=2, shrink=3)

    construct_from_another(first,
            fields=['space', 'stretch', 'shrink'],
            )

def test_glue_and_leader_getstate():

    for spec, expected in [
            ("12sp", [12]),
            ("12sp plus 2sp", [12, 2, 0]),
            ("12sp minus 3sp", [12, 0, 0, 3, 0]),
            ("12sp plus 2sp minus 3sp", [12, 2, 0, 3, 0]),
            ("12sp plus 2fil minus 3sp", [12, 2*65536, 1, 3, 0]),
            ("12sp plus 2fil minus 3fill", [12, 2*65536, 1, 3*65536, 2]),
            ("12sp plus 2fil minus 3filll", [12, 2*65536, 1, 3*65536, 3]),
            ]:
        glue = get_glue(spec+'q', raw=True)
        glue_found = glue.__getstate__()

        assert glue_found==expected, spec

        leader = yex.box.Leader(glue=glue)
        leader_found = leader.__getstate__()

        if len(expected)==1:
            expected = expected[0]

        assert leader_found==expected, spec

def test_glue_pickle():

    for spec, expected in [
            ("12sp", [12]),
            ("12sp plus 2sp", [12, 2, 0]),
            ("12sp minus 3sp", [12, 0, 0, 3, 0]),
            ("12sp plus 2sp minus 3sp", [12, 2, 0, 3, 0]),
            ("12sp plus 2fil minus 3sp", [12, 2*65536, 1, 3, 0]),
            ("12sp plus 2fil minus 3fill", [12, 2*65536, 1, 3*65536, 2]),
            ("12sp plus 2fil minus 3filll", [12, 2*65536, 1, 3*65536, 3]),
            ]:

        glue = get_glue(spec+'q', raw=True)

        pickle_test(
                glue,
                [
                    (lambda v: (v.__getstate__(), expected),
                        spec),
                    ],
                )

    pickle_test(
            Dimen(23, 'fill',
                can_use_fil = True,
                ),
            [
                (
                    lambda v: (float(v), 23),
                    'width',
                    ),
                (
                    lambda v: (v.infinity, 2),
                    'infinity',
                    ),
                ],
            )

def test_glue_actual_value():
    doc = yex.Document()

    glue = yex.value.Glue(space=yex.value.Dimen(123, 'pt'))
    e = doc.open('')

    e.push(glue)

    found = yex.value.Glue.from_tokens(e)

    assert found.space==yex.value.Dimen(123, 'pt')
