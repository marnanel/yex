"""
Debugging controls.
"""

from yex.control.control import Unexpandable

class Debugging(Unexpandable): pass

class Error_handling_mode(Debugging):
    pass

class Scrollmode(Error_handling_mode):
    pass
class Nonstopmode(Error_handling_mode):
    pass
class Batchmode(Error_handling_mode):
    pass
class Errorstopmode(Error_handling_mode):
    pass

class Dump(Unexpandable):
    horizontal = 'vertical'
    vertical = True
