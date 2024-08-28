import logging as builtin_logging
from logging import DEBUG, INFO, WARN, WARNING, ERROR, CRITICAL
import sys
import os

ALL = 'all'
NONE = 'none'
LIST= 'list'

MAGIC = { ALL, NONE, LIST }

DEFAULT = 'all'

ENVIRON = 'YEX_LOGGERS'

class Loggers:
    names = set(MAGIC)

    @classmethod
    def selectLoggers(cls, handlers, verbosity=0):
        builtin_logger = builtin_logging.getLogger('yex')

        builtin_logger.addHandler(
                builtin_logging.StreamHandler(sys.stdout))

        if handlers is None:
            try:
                handlers = os.environ[ENVIRON]
            except KeyError:
                handlers = DEFAULT

        requested = set(handlers.split(','))

        if LIST in requested:
            for name in sorted(cls.names):
                print(f'  {name}')
            sys.exit(255)

        if NONE in requested:
            requested.remove(NONE)

        if ALL in requested:
            requested = cls.names - MAGIC - requested

        if verbosity>1:
            level = DEBUG
        elif verbosity>0:
            level = INFO
        else:
            level = WARNING

        for handler in sorted(requested):
            sublogger = cls.getLogger(handler)
            sublogger.setLevel(level)

    @classmethod
    def getLogger(cls, name):
        cls.names.add(name)

        assert name not in (ALL, NONE, LIST)

        result = builtin_logging.getLogger(f'yex.general.{name}')

        return result

getLogger = Loggers.getLogger
selectLoggers = Loggers.selectLoggers

__all__ = [
        'LOGGERS',
        'ALL', 'NONE', 'LIST',
        'DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL',
        'getLogger',
        'selectLoggers',
        ] + list(MAGIC)
