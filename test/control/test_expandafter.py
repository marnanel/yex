import yex
from test import *

def test_expandafter():
    assert run_code(
            setup=(
                r'\def\myis#1#2{My #1 is #2}'
                r'\def\butunbowed{ but unbowed}'
                ),

            call=(
                r'\expandafter\butunbowed\myis{head}{bloody}.'
                ),
            find='ch',
            )=='My head is bloody but unbowed.'
