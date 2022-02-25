from mex.control.table import ControlsTable
from mex.control.macro import *

__all__ = [
        'ControlsTable',

        'Macro',
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
        'C_StringMacro',
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
            value!=Macro and
            issubclass(value, Macro) and
            not name.startswith('C_')
            ])

    return result
