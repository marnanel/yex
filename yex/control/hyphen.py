"""
Hyphenation controls.
"""

from yex.control.control import C_Unexpandable
import yex

@yex.decorator.control()
def Hyphenation(): pass
@yex.decorator.control()
def Patterns(): pass
@yex.decorator.control()
def Setlanguage(): pass
