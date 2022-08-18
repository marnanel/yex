import yex
from test import *
import pytest

def test_exception_simple():
    d = yex.value.Dimen()

    with pytest.raises(yex.exception.CantAddError):
        d = d + 1

def test_exception_t():
    r"""
    Tests "x (which is a type(x))"

    ...which is implemented by t() in yex.exception,
    hence the name of the test.
    """
    class CreatureError(yex.exception.YexError):
        form = 'I saw a large {t(creature)}'
        code = 'CREATURE'

    class Mammal:
        def __init__(self, species):
            self.species = species
        def __str__(self):
            return f'hairy {self.species}'

    w = Mammal('wombat')

    try:
        raise CreatureError(
                creature = w,
                )
    except CreatureError as ce:
        result = str(ce)

    assert result=='I saw a large hairy wombat (which is a Mammal)'

    try:
        raise CreatureError(
                creature = 'EOF',
                )
    except CreatureError as ce:
        result = str(ce)

    assert result=='I saw a large end of file'
