__title__ = 'yex'
__version__ = '0.1.4'
VERSION = __version__
__author__ = 'Marnanel Thurman'
__license__ = 'GPL-2'
__copyright__ = 'Copyright (c) 2022 Marnanel Thurman'

import yex.decorator
import yex.output
import yex.control
import yex.mode
from yex.document.document import Document
from yex.module import make_module_into_yexmodule

def _add_logging_level_trace():
    import logging
    logging.TRACE = 5
    logging.addLevelName(logging.TRACE, 'TRACE')
    def _log_trace(self, message, *args, **kwargs):
        if self.isEnabledFor(logging.TRACE):
            self._log(logging.TRACE, message, args, **kwargs)
    logging.Logger.trace = _log_trace

_add_logging_level_trace()

make_module_into_yexmodule(__name__)

__all__ = [
        'Document',
        ]
