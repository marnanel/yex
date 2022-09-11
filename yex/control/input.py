"""
Input/output controls.

These deal with access to files and streams.
"""
import logging
from yex.control.control import *
import yex

logger = logging.getLogger('yex.general')

@yex.decorator.control()
def Input(fn: yex.filename.Filename, tokens):
    f = open(str(fn), 'r')
    inner = tokens.doc.open(f)
    tokens.delegate = inner

@yex.decorator.control()
def Endinput():
    raise NotImplementedError()
