from yex.output.superclass import *
from yex.output.svg import *

g = list(globals().items())

def get_driver_for(doc, filename, format=None):

    # stub
    if format not in (None, 'svg'):
        raise ValueError(f"unknown format: {format}")

    return Svg(
            doc = doc,
            filename = filename,
            )

DEFAULT_FORMAT = 'svg'

__all__ = list([
    name for name, value in g
    if value.__class__==type and
    issubclass(value, Output)
    ])
