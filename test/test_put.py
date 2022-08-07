import pytest
import tempfile
import os
import glob
import yex
from test import *

def test_put_simple():

    doc = yex()

    assert isinstance(doc, yex.Document)

def test_put_target():

    dirname = tempfile.mkdtemp()
    target_filename = os.path.join(dirname, 'wombat.html')

    yex.put.put('wombat',
            target = target_filename,
            )

    with open(target_filename, 'r') as f:
        contents = f.read()

    for f in glob.glob(os.path.join(dirname, '*')):
        os.unlink(f)
    os.rmdir(dirname)

    assert contents.startswith('<!DOCTYPE html>'), contents
    assert 'wombat</span>' in contents, contents
