"""
Logging controls.

These same classes are both yex controls and ordinary Python logging filters.
"""
import logging
import sys
from yex.control.parameter import NumberParameter

yex_logger = logging.getLogger('yex')
logger = logging.getLogger('yex.general')

class TracingParameter(NumberParameter):
    """
    Parameters which switch various kinds of logging on and off.
    """
    is_queryable = True

    def _output(self, s):
        """
        Actually emits a tracing record.

        At the moment, it just prints it to stdout.

        You can monkeypatch this method in testing.
        """
        print(s) # for now

    def info(self, s):
        """
        Outputs a string, if we feel it's important to do so.

        This will probably eventually be integrated with python's
        logging system.

        """
        raise NotImplementedError()

class Tracingonline(TracingParameter):
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

    @TracingParameter.value.setter
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

class TracingFilter(TracingParameter):

    initial_value = 0

    def info(self, s):
        if self._value>=1:
            self._output(s)

class Tracingmacros(TracingFilter):
    "Macros, as they are expanded"

class Tracingstats(TracingFilter):
    "Statistics about memory usage"

class Tracingparagraphs(TracingFilter):
    "Line-break calculations"

class Tracingpages(TracingFilter):
    "Page-break calculations"

class Tracingoutput(TracingFilter):
    "Boxes that are shipped out"

class Tracinglostchars(TracingFilter):
    "Characters not in the font"

class Tracingcommands(TracingFilter):
    "Commands before they are executed"

    def __init__(self, doc):
        super().__init__(doc)
        self._previous_mode = None

    def info(self, s):
        self._output(s)

    def notice_item(self, item, mode):
        if self._value==0:
            return
        elif self._value==1:
            pass # FIXME
        else:
            pass # FIXME

        line = '{'
        if mode!=self._previous_mode:
            line += mode.name+' mode: '
            self._previous_mode = mode

        if hasattr(item, 'meaning'):
            line += item.meaning
        else:
            line += str(item)

        line += '}'

        self._output(line)

class Tracingrestores(TracingFilter):
    "Deassignments when groups end"
