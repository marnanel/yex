"""
Debugging controls.
"""

from yex.control.control import C_Unexpandable

class C_Debugging(C_Unexpandable): pass

class C_Error_handling_mode(C_Debugging):
    pass

class Scrollmode(C_Error_handling_mode):
    pass
class Nonstopmode(C_Error_handling_mode):
    pass
class Batchmode(C_Error_handling_mode):
    pass
class Errorstopmode(C_Error_handling_mode):
    pass

class Dump(C_Unexpandable):
    horizontal = 'vertical'
    vertical = True
