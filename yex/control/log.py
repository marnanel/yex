"""
Logging controls.

These same classes are both yex controls and ordinary Python logging filters.
"""
import logging
import sys
from yex.control.parameter import C_NumberParameter

yex_logger = logging.getLogger('yex')
logger = logging.getLogger('yex.general')

class C_TracingParameter(C_NumberParameter):
    """
    Parameters which switch various kinds of logging on and off.
    """
    is_queryable = True

class Tracingonline(C_TracingParameter):
    """
    If positive, logs go to stdout; otherwise they go to the logfile.

    (The name is a holdover from TeX; it meant something
    different in the 1980s.)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Is a file handler already set up?
        self._value = 1
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                self._value = 0
                break

        self._stdout_handler = None
        self._file_handler = None

        self.logging_filename = 'yex.log'

    def _clear_handlers(self):
        for handler in yex_logger.handlers:
            yex_logger.removeHandler(handler)

    @C_TracingParameter.value.setter
    def value(self, n):

        self._value = n
        self._clear_handlers()

        if n>0:
            yex_logger.addHandler(self.stdout_handler)
        else:
            yex_logger.addHandler(self.file_handler)

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

class C_TracingFilter(C_TracingParameter):

    initial_value = 0

    def info(self, s):
        if self._value>=1:
            print(s)

class Tracingmacros(C_TracingFilter):
    "Macros, as they are expanded"

class Tracingstats(C_TracingFilter):
    "Statistics about memory usage"

class Tracingparagraphs(C_TracingFilter):
    "Line-break calculations"

class Tracingpages(C_TracingFilter):
    "Page-break calculations"

class Tracingoutput(C_TracingFilter):
    "Boxes that are shipped out"

class Tracinglostchars(C_TracingFilter):
    "Characters not in the font"

class Tracingcommands(C_TracingFilter):
    "Commands before they are executed"

class Tracingrestores(C_TracingFilter):
    "Deassignments when groups end"
