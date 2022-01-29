import logging
import sys
import mex.parameter

mex_logger = logging.getLogger('mex')
mex_logger.propagate = False

class TracingParameter(mex.parameter.Parameter):
    """
    These are classes representing TeX parameters.
    You can find the list on p269 of the TeXbook.
    """
    def __init__(self,
            state,
            value = 0):
        super().__init__(
                value = value,
                )
        self.state = state

class Online(TracingParameter):
    """
    If positive, logs go to stdout; otherwise they go
    to the logfile.

    (The name is a holdover from TeX; it meant something
    different in the 1980s.)
    """

    initial_value = 1 # log to stdout

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._stdout_handler = None
        self._file_handler = None

        self.logging_filename = 'mex.log'

        # Note that we're assuming value!=0 (which is what
        # names() always passes in). When Python's logging
        # system starts up, the stdout handler is always
        # in place, and we do nothing to remove it.

    @TracingParameter.value.setter
    def value(self, n):
        if n>0:
            mex_logger.addHandler(self.stdout_handler)

            if self._file_handler is not None:
                mex_logger.removeHandler(self.file_handler)
        else:
            mex_logger.removeHandler(self.stdout_handler)
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
        result = Online(
                state = self.state,
                value = self._value,
                )

        result._stdout_handler = self._stdout_handler
        result._file_handler = self._file_handler
        result.logging_filename = self.logging_filename

        return result

class TracingFilter(TracingParameter):

    initial_value = 0

    @mex.parameter.Parameter.value.setter
    def value(self, n):
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
    pass

class Paragraphs(TracingFilter):
    "Line-break calculations"
    pass

class Pages(TracingFilter):
    "Page-break calculations"
    pass

class Output(TracingFilter):
    "Boxes that are shipped out"
    pass

class Lostchars(TracingFilter):
    "Characters not in the font"
    pass

class Commands(TracingFilter):
    "Commands before they are executed"
    pass

class Restores(TracingFilter):
    "Deassignments when groups end"
    pass

def names(state):

    result = dict([
        ('tracing'+name.lower(),
            value(state, value.initial_value)) for
        (name, value) in globals().items()
        if value.__class__==type and
        issubclass(value, TracingParameter) and
        not name.startswith('Tracing')
        ])
    
    return result
