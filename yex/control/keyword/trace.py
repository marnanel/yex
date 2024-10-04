"""
Tracing controls.
"""
import logging
import sys
from yex.control.parameter import NumberParameter
import yex

logger = yex.logging.getLogger('control')

class TracingParameter(NumberParameter):
    """
    Parameters which switch various kinds of tracing on and off.
    """

    is_queryable = True
    initial_value = 0

    def info(self, s):
        """
        Outputs a string, if we feel it's important to do so.
        """
        if self._value>=1:
            self._output(s)

    def info(self, s):
        raise NotImplementedError()

class Tracingonline(TracingParameter):
    """
    If positive, tracing goes to stdout; otherwise they go to the logfile.

    (The name is a holdover from TeX; it meant something
    different in the 1980s.)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Is a file handler already set up?
        self._value = 1
        for handler in logger.handlers:
            if isinstance(handler, tracing.FileHandler):
                self._value = 0
                break

        self._stdout_handler = None
        self._file_handler = None

        self.tracing_filename = 'yex.log'

    def _clear_handlers(self):
        for handler in lang_logger.handlers:
            lang_logger.removeHandler(handler)

    @TracingParameter.value.setter
    def value(self, n):

        self._value = n
        self._clear_handlers()

        if n>0:
            lang_logger.addHandler(self.stdout_handler)
        else:
            lang_logger.addHandler(self.file_handler)

    @property
    def stdout_handler(self):
        if self._stdout_handler is None:
            self._stdout_handler = tracing.StreamHandler(
                    stream=sys.stdout,
                    )
        return self._stdout_handler

    @property
    def file_handler(self):
        if self._file_handler is None:
            self._file_handler = tracing.FileHandler(
                    filename = self.tracing_filename,
                    encoding = 'UTF-8',
                    )
        return self._file_handler

class Tracingmacros(TracingParameter):
    "Macros, as they are expanded"

class Tracingstats(TracingParameter):
    "Statistics about memory usage"

class Tracingparagraphs(TracingParameter):
    "Line-break calculations"

class Tracingpages(TracingParameter):
    "Page-break calculations"

class Tracingoutput(TracingParameter):
    "Boxes that are shipped out"

class Tracinglostchars(TracingParameter):
    "Characters not in the font"

class Tracingcommands(TracingParameter):
    "Commands before they are executed"

    initial_value = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._previous_mode = None

    def info(self, s):
        self._output(s)

    def _maybe_notice_mode(self, mode):
        if mode is not None and mode!=self._previous_mode:
            self._previous_mode = mode
            return mode.name+' mode: '
        else:
            return ''

    def notice_item(self, item, mode=None):
        if self._value<1:
            return

        if hasattr(item, 'from_human') and not item.from_human:
            return

        if isinstance(item, yex.control.keyword.Par):
            # We ignore Par, because all it does is
            # generate a Paragraph token, which we'll
            # see immediately.
            #
            # If we left it in, we'd output {par} {par}.
            # If we filtered out the Paragraph token, which
            # on the face of it would make more sense because
            # it's yex-specific, we would confuse the mode-change
            # detection.
            return

        line = '{' + self._maybe_notice_mode(mode)

        if hasattr(item, 'meaning'):
            line += item.meaning
        else:
            line += str(item)

        line += '}'

        self._output(line)

    def notice_conditional(self, message, mode=None):
        if self._value<2:
            return

        line = (
                '{' +
                self._maybe_notice_mode(mode) +
                message +
                '}'
                )

        self._output(line)

class Tracingrestores(TracingParameter):
    "Deassignments when groups end"
