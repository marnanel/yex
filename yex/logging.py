r"""
Yex's logging facilities.

We define two kinds of loggers within Python's built-in logging
system. This module is concerned with `yex.general.*`, for
debugging yex itself. `yex.lang.*`, for TeX's own logging system,
is handled in `yex.control.keyword.log`.

All level identifiers from Python's built-in logging are
exported from this module.

### Calling the loggers, from Python code

They are accessed like Python's built-in logging, using
`Loggers.getLogger()`, except that its argument is only
the element which follows `yex.general.`-- for example,
`Loggers.getLogger('parse')`.

If you log a string, and the string begins with `>`, subsequent
logs for all loggers will be indented by one space. If the
string instead begins with `<`, and you have previously added
any indent, the logs will be dedented by one space.

## Selecting the loggers, as a user

They can be selected using the `-l` or `--loggers` switches
to yex's main program. Alternatively, they can be selected
using the environment variable `YEX_LOGGERS`. The commandline
switches override any settings in the environment variable.
In each case, the selection is a list of logger names separated
by commas without spaces.

There are also four "magic" loggers, which can be selected by
the user but not accessed using `Loggers.getLogger()`:

    - `all` selects all loggers. If it is combined with other
        logger names, the others will have negative effect
        (for example, `all,parse` selects everything but `parse`.)
    - `none` selects no loggers except those explicitly specified.
    - `list` prints a list of loggers to standard output,
        including the magic loggers, then exits with errorlevel 255.
    - `verbose` sets the level of all `yex.general.*` loggers to
        `DEBUG`. Without this setting, it will be `INFO`.

If any of the names given by the user does not belong to any logger,
we print an error message to stderr and exit with errorlevel 254.

"""
import logging as builtin_logging
from logging import DEBUG, INFO, WARN, WARNING, ERROR, CRITICAL
import sys
import os
import textwrap

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
    def selectLoggers(cls, handlers):
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
            sys.exit(254)

        if LIST in requested:
            for name in sorted(cls.names):
                print(f'  {name}')
            sys.exit(255)

        if NONE in requested:
            requested.remove(NONE)

        verbose = VERBOSE in requested
        if verbose:
            requested.remove(VERBOSE)

        if ALL in requested:
            requested = cls.names - MAGIC - requested

        for handler in sorted(cls.names):

            if handler in MAGIC:
                continue

            sublogger = cls.getLogger(handler)
            if handler not in requested:
                sublogger.setLevel(WARNING)
            elif verbose:
                sublogger.setLevel(DEBUG)
            else:
                sublogger.setLevel(INFO)

    @classmethod
    def getLogger(cls, name):
        cls.names.add(name)

        assert name not in (ALL, NONE, LIST)

        result = builtin_logging.getLogger(f'yex.general.{name}')

        return result

class MainLoggingFormatter(builtin_logging.Formatter):

    blank_column = ' ' * 14

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

        message = f'\n{self.blank_column}'.join(textwrap.wrap(
                message,
                ))

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
