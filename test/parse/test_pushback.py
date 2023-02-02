import pytest
import yex
from test import *

def drain(pb, expected, why=None):

    assert pb.items == list(reversed(expected))

    found = []
    while True:
        item = pb.pop()
        if item is None:
            break
        found.append(item)
    assert found==expected, why

def test_pushback_push_nothing():
    doc = yex.Document()
    pb = doc.pushback

    drain(pb, expected=[])

def test_pushback_push_char():
    doc = yex.Document()
    pb = doc.pushback

    pb.push('a')
    drain(pb, expected=['a'], why='just one char')

def test_pushback_push_string():
    doc = yex.Document()
    pb = doc.pushback

    pb.push('fred')
    drain(pb, expected=['f', 'r', 'e', 'd'],
            why='strings are broken up and pushed in order',
            )

def test_pushback_push_two_strings():
    doc = yex.Document()
    pb = doc.pushback

    pb.push('ma')
    pb.push('wil')
    drain(pb, expected=['w', 'i', 'l', 'm', 'a'],
            why='pushing two strings reverses them both separately'
            )

def test_pushback_push_none():
    doc = yex.Document()
    pb = doc.pushback

    pb.push('ma')
    pb.push(None)
    pb.push('wil')
    drain(pb, expected=['w', 'i', 'l', 'm', 'a'],
            why='pushing None does nothing')

def test_pushback_push_list():
    doc = yex.Document()
    pb = doc.pushback

    pb.push([1,2,3])
    pb.push(4)
    drain(pb, expected=[4, 1, 2, 3],
            why='lists are broken up and pushed in order',
            )

def test_pushback_push_other_iterable():
    doc = yex.Document()
    pb = doc.pushback

    pb.push(1)
    pb.push( (2,3) )
    pb.push(4)
    drain(pb, expected=[4, (2, 3), 1],
            why='iterables other than str or list are handled as objects')

def test_pushback_adjust_group_depth():
    doc = yex.Document()
    pb = doc.pushback

    for item, reverse, expected in [
            ('a', False, 0),
            ('a', True, 0),

            ('{', False, 1),
            ('{', True, 0),
            ('}', False, -1),
            ('}', True, 0),

            (yex.parse.Letter('a'), False, 0),
            (yex.parse.Letter('a'), True, 0),

            (yex.parse.BeginningGroup('{'), False, 1),
            (yex.parse.BeginningGroup('{'), True, 0),
            (yex.parse.EndGroup('}'), False, -1),
            (yex.parse.EndGroup('}'), True, 0),

            ]:
        pb.adjust_group_depth(
               c = item,
               reverse = reverse,
               )
        assert pb.group_depth==expected, f"c={item}, reverse={reverse}"

def test_pushback_close():
    doc = yex.Document()
    pb = doc.pushback

    pb.close()

    with pytest.raises(ValueError):
        pb.adjust_group_depth('{')
        pb.close()

    pb.adjust_group_depth('}')
    pb.close()
