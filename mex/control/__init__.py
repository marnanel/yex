from mex.control.word import *
from mex.control.table import *
from mex.control.macro import *
from mex.control.conditional import *
from mex.control.register import *
from mex.control.string import *
from mex.control.arithmetic import *
from mex.control.other import *

__all__ = [
        'ControlsTable',
        'ControlWord',

        'C_ControlWord',
        'C_UserDefined',
        'Def',
        'Outer',
        'Gdef',
        'Outer',
        'Long',
        'Edef',
        'Xdef',
        'Global',
        'C_Defined',
        'Chardef',
        'Mathchardef',
        'Par',
        'C_StringControl',
        'Message',
        'Errmessage',
        'Special',
        'Countdef',
        'Dimendef',
        'Skipdef',
        'Muskipdef',
        'Toksdef',
        'Advance',
        'Multiply',
        'Divide',
        'The',
        'Let',
        'Font',
        'Relax',
        'Hbox',
        'Vbox',
        'Noindent',
        'Indent',

        'C_Conditional',
        'Iftrue',
        'Iffalse',
        'Ifnum',
        'Ifdim',
        'Ifodd',
        '_Ifmode',
        'Ifvmode',
        'Ifhmode',
        'Ifmmode',
        'Ifinner',
        'If',
        'Ifcat',
        'Fi',
        'Else',
        'Ifcase',
        'Or',
        'Noexpand',
        'Showlists',
                ]

def handlers():

    # Take a copy. Sometimes evaluating a macro may
    # create another macro, which changes the size
    # of globals().items() and confuses the list comprehension.
    g = list(globals().items())

    result = dict([
            (name.lower(), value()) for
            (name, value) in g
            if value.__class__==type and
            value!=mex.control.word.C_ControlWord and
            issubclass(value, mex.control.word.C_ControlWord) and
            not name.startswith('C_')
            ])

    return result
