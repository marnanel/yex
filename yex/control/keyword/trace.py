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
        self._output(s)

    def _output(self, s):
        """
        Outputs a string, if we feel it's important to do so.
        """
        if self._value>=1:
            yex.io.trace(s)

class Tracingonline(TracingParameter):
    """
    If positive, tracing goes to stdout; otherwise they go to the logfile.

    (The name is a holdover from TeX; it meant something
    different in the 1980s.)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._file_handler = None
        self.tracing_filename = 'yex.log'

    @TracingParameter.value.setter
    def value(self, n):

        self._value = n

        if n>0:
            yex.io.trace.to_stdout = True
        else:
            yex.io.trace.to_stdout = False

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

        self.info(line)

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
