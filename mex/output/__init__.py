from mex.output.superclass import *
from mex.output.svg import *

g = list(globals().items())

def get_default():
    return Svg # for now

__all__ = list([
    name for name, value in g
    if value.__class__==type and
    issubclass(value, Output)
    ])
