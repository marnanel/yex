from yex.output.output import *
from yex.output.svg import *

g = list(globals().items())

DEFAULT_DRIVER = Svg

def get_driver_for(doc, filename, format=None):

    import os, yex

    if filename is None:
        return DEFAULT_DRIVER(doc=doc, filename='')
    elif isinstance(format, Output):
        return format
    elif isinstance(format, type):
        return format(doc=doc, filename=filename)
    elif format is None:
        _, format = os.path.splitext(filename)

    if format.startswith('.'):
        format = format[1:]

    capable = [
        driver for name, driver in g
        if driver.__class__==type and
        issubclass(driver, Output)
        and driver!=Output
        and driver.can_handle(format)
        ]

    if len(capable)==0:
        raise yex.exception.YexError(f'unknown format: {format}')
    elif len(capable)>1:
        print(f'warning: there are multiple drivers which '
                f'can handle {format}:',
            ', '.join([x.__class__.__name__ for x in capable]),
            '-- using ',capable[0].__class__.__name__,
                )

    return capable[0](
            doc = doc,
            filename = filename,
            )

__all__ = list([
    name for name, value in g
    if value.__class__==type and
    issubclass(value, Output)
    ])
