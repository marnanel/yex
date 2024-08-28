import logging as builtin_logging
from logging import DEBUG, INFO, WARN, WARNING, ERROR, CRITICAL
import sys
import os

ALL = 'all'
NONE = 'none'
LIST = 'list'
VERBOSE = 'verbose'

MAGIC = { ALL, NONE, LIST, VERBOSE }

DEFAULT = 'all'

ENVIRON = 'YEX_LOGGERS'

class Loggers:
    names = set(MAGIC)

    @classmethod
    def selectLoggers(cls, handlers, verbosity=0):
        builtin_logger = builtin_logging.getLogger('yex')

        stream_handler = builtin_logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(MainLoggingFormatter())

        builtin_logger.addHandler(stream_handler)

        if handlers is None:
            try:
                handlers = os.environ[ENVIRON]
                source = f'environment variable {ENVIRON}'
            except KeyError:
                handlers = DEFAULT
                source = 'default'
        else:
            source = 'command line'

        requested = set(handlers.split(','))

        unknown = requested - cls.names

        if unknown:
            print("yex: these names are unknown:")
            print("yex:   " + ' '.join(sorted(unknown)))
            print(f"yex: (from {source})")
            print("yex: For a list, do '--loggers list'.")
            sys.exit(253)

        if LIST in requested:
            for name in sorted(cls.names):
                print(f'  {name}')
            sys.exit(255)

        if NONE in requested:
            requested.remove(NONE)

        if VERBOSE in requested:
            requested.remove(VERBOSE)
            verbosity = max(verbosity, 2)

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

class MainLoggingFormatter(builtin_logging.Formatter):

    def __init__(self):
        super().__init__()
        self.indent = 2

    def format(self, record):
        logger = record.name.replace('yex.general.', '')[:3]

        if record.levelno!=builtin_logging.DEBUG:
            level_letter = record.levelname[0]
        else:
            level_letter = ' '

        module = record.pathname
        last_slash = module.rfind('/')
        if last_slash!=-1:
            module = module[last_slash+1:-3][:6] # remove ".py"

        message = record.msg % record.args

        return (
                f'{logger:4}{level_letter} {module:6}'
                f'{record.lineno:5}{" " * self.indent}{message}'
                )

getLogger = Loggers.getLogger
selectLoggers = Loggers.selectLoggers

__all__ = [
        'LOGGERS',
        'DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL',
        'getLogger',
        'selectLoggers',
        ] + list(MAGIC)
