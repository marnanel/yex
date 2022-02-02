import logging
import sys
import mex.parameter

mex_logger = logging.getLogger('mex')

class TracingParameter(mex.parameter.Parameter):
    """
    These are classes representing TeX parameters.
    You can find the list on p269 of the TeXbook.
    """
    def __init__(self,
            state):
        super().__init__(
                value = 0,
                )
        self.state = state

class Online(TracingParameter):
    """
    If positive, logs go to stdout; otherwise they go
    to the logfile.

    (The name is a holdover from TeX; it meant something
    different in the 1980s.)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Is a file handler already set up?
        self._value = 1
        for handler in mex_logger.handlers:
            if isinstance(handler, logging.FileHandler):
                self._value = 0
                break

        self._stdout_handler = None
        self._file_handler = None

        self.logging_filename = 'mex.log'

    def _clear_handlers(self):
        for handler in mex_logger.handlers:
            mex_logger.removeHandler(handler)

    @TracingParameter.value.setter
    def value(self, n):

        self._clear_handlers()

        if n>0:
            mex_logger.addHandler(self.stdout_handler)
        else:
            mex_logger.addHandler(self.file_handler)

    @property
    def stdout_handler(self):
        if self._stdout_handler is None:
            self._stdout_handler = logging.StreamHandler(
                    stream=sys.stdout,
                    )
        return self._stdout_handler

    @property
    def file_handler(self):
        if self._file_handler is None:
            self._file_handler = logging.FileHandler(
                    filename = self.logging_filename,
                    encoding = 'UTF-8',
                    )
        return self._file_handler

    def __deepcopy__(self, memo):
        return self

class TracingFilter(TracingParameter):

    initial_value = 0

    @mex.parameter.Parameter.value.setter
    def value(self, n):

        self._value = n

        logger = mex_logger.getChild(
                self.__class__.__name__.lower())

        if n>1:
            logger.setLevel(logging.DEBUG)
        elif n==1:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)

class Macros(TracingFilter):
    "Macros, as they are expanded"

class Stats(TracingFilter):
    "Statistics about memory usage"

class Paragraphs(TracingFilter):
    "Line-break calculations"

class Pages(TracingFilter):
    "Page-break calculations"

class Output(TracingFilter):
    "Boxes that are shipped out"

class Lostchars(TracingFilter):
    "Characters not in the font"

class Commands(TracingFilter):
    "Commands before they are executed"

class Restores(TracingFilter):
    "Deassignments when groups end"

def names(state):

    result = dict([
        ('tracing'+name.lower(),
            value(state)) for
        (name, value) in globals().items()
        if value.__class__==type and
        issubclass(value, TracingParameter) and
        not name.startswith('Tracing')
        ])
    
    return result
