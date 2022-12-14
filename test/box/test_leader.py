import logging
import yex
import pytest
from test import *

logger = logging.getLogger('yex.general')

def test_leader_from_another():
    glue = yex.value.Glue(
            space=1, stretch=2, shrink=3)
    first = yex.box.Leader(
            glue = glue)

    construct_from_another(first,
            fields=['glue'],
            )

def test_leader_from_glue():
    glue = yex.value.Glue(space=1, stretch=2, shrink=3)

    fred = yex.box.Leader(glue)
    assert float(fred.space)==1
    assert float(fred.stretch)==2
    assert float(fred.shrink)==3

    fred = yex.box.Leader(glue=glue)
    assert float(fred.space)==1
    assert float(fred.stretch)==2
    assert float(fred.shrink)==3

def test_leader_from_document():
    doc = yex.Document()

    for field in [r'\leftskip']:
        for length in [0, 10, 20, 30]:
            doc[field] = yex.value.Glue(length, 'pt')
            fred = yex.box.Leader(field, doc=doc)

            assert float(fred.space)==length, f'doc["{field}"]=={length}pt'

        with pytest.raises(AssertionError):
            fred = yex.box.Leader(field) # no doc=doc

    with pytest.raises(KeyError):
        fred = yex.box.Leader(r'\wombat', doc=doc)

def test_leader_silly_value():
    with pytest.raises(TypeError):
        fred = yex.box.Leader(glue={'silly': True})

def test_leader_set_length():
    glue = yex.value.Glue(space=1, stretch=2, shrink=3)
    fred = yex.box.Leader(glue)
    assert fred.width==1
    assert fred.height==0
    assert fred.depth==0

    fred.length=50
    assert fred.width==50
    assert fred.height==0
    assert fred.depth==0

    barney = yex.box.Leader(glue, vertical=True)
    assert barney.width==0
    assert barney.height==1
    assert barney.depth==0

    barney.length=50
    assert barney.width==0
    assert barney.height==50
    assert barney.depth==0
