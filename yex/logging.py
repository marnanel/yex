r"""
Yex's logging facilities.

This module is concerned with `yex.general.*`, for
debugging yex itself. TeX's own logging system is handled
separately; see `yex.control.keyword.log` for that.

## Calling the loggers, from Python code

They are accessed like Python's built-in logging, using
`Loggers.getLogger()`, except that its argument is only
the element which follows `yex.general.`-- for example,
`Loggers.getLogger('parse')`.

There are a few special markup tricks:

    - If the string begins with `>`, subsequent logs for *all*
      loggers will be indented by two spaces, beginning
      at the current line.
    - If the string begins with `<`, it undoes the effect
      of one previous `<` (if any).
    - If the string begins with `=`, it is indented by
      two spaces, but it doesn't affect any following strings.
    - If the string begins with `[` and contains `]:`, then
      that whole prefix is removed, and the part between
      the two brackets becomes the "context"-- see below.
      If you mix this with the indentation commands, then
      the indentation commands should come first.

## Reading the logs

```
exp W expand  271   spawning another Expander with changes: {'on_eof': 'none'}; called
                \   from format (__init__.py:953)
```
 - `exp` is the logger in use (here, `expander`).
 - `W` is the first letter of the logging loglevel-- here, contrived,
   it's WARNING. However, DEBUG is shown as a space to reduce clutter
 - `expand` is the first six letters of the name of the Python module.
   Here, it's `yex.parse.expander`.
 - `271` is the line number.
 - The rest of the line is the message. It's wordwrapped to `WRAP_WIDTH`.
   If it continues beyond the first line, the subsequent lines
   are marked with `\`.

```
exp   expand  319--[exp.53c8;bounded;exhaust;deep;no_outer;ls=M;s=<str>;l=1;c=12]
                       -- found {
exp   expand  332--[exp.53c8;bounded=1;exhaust;deep;no_outer;ls=M;s=<str>;l=1;c=12]
                          -- opens bounded expansion, read again
exp   expand  263   not spawning another Expander; no changes requested (called from
                \   format (__init__.py:953))
```

If a context string is given (see above), it is shown with a prefix of `--`,
followed by the rest of the message. But if the previous context *for this logger*
is exactly the same, the context will be ignored.

In the example above, the same Expander produces a different context string for the
second line, because it's moved on one space through the document. But on the third
line, nothing has changed, so the Expander has sent the same context as for the
line before. Thus the logging system ignores the context.

## Selecting the loggers, as a user running yex

Loggers can be selected using the `-l` or `--loggers` switches
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
    - `verbose` sets the loglevel of all `yex.general.*` loggers to
        `DEBUG`. Without this setting, it will be `INFO`.

If any of the names given by the user are unknown,
we print an error message to stderr and exit with errorlevel 254.

All loglevel identifiers exported by Python's built-in logging are
also exported from this module.

The `y` script turns on some loggers automatically if you give it
a substring to match in test names. See its documentation.
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

WRAP_WIDTH = 70

class Loggers:
    names = set(MAGIC)

    @classmethod
    def selectLoggers(cls, handlers):
        """
        Sets the loglevel of all the yex.general loggers.

        This behaves as described in this module's docstring.

        Note that "turning a logger off" means setting its
        loglevel to WARNING, and "turning a logger on" means
        setting its level to DEBUG if "verbose" is off, and
        INFO otherwise.

        Args:
            handlers (str or None): a comma-separated list
                of handlers; see this module's docstring for
                details of the format.

                If this is None, we will look in the environment
                variable given by `ENVIRON`.

        Returns:
            None
        """
        builtin_logger = builtin_logging.getLogger('yex')

        # Remove existing handlers. (Test harnesses will leave them in.)
        for handler in builtin_logger.handlers:
            builtin_logger.removeHandler(handler)

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
        r"""
        Gets the yex logger with the given name.

        That is, `yex.logger.` plus the given string.
        As a side effect, this causes the string to become
        a valid name for a logger. For example, it will be
        printed if the user does `yex -L list`.

        Args:
            name (str): the name of the logger

        Raises:
            ValueError: if name refers to a "magic" logger,
                like `"all"`

        Returns:
            Logger
        """
        if name in MAGIC:
            raise ValueError(f"Not a valid logger name: {name}")

        cls.names.add(name)


        result = builtin_logging.getLogger(f'yex.general.{name}')

        return result

class MainLoggingFormatter(builtin_logging.Formatter):

    blank_column = ' ' * 14

    def __init__(self):
        super().__init__()
        self.__indent = 0
        self.__context = {}

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

        temporary_indent = False

        if message.startswith('>'):
            self.__indent += 1
            message = message[1:]
        elif message.startswith('<'):
            if self.__indent>0:
                self.__indent -= 1
            message = message[1:]
        elif message.startswith('='):
            self.__indent += 1
            temporary_indent = True
            message = message[1:]

        context_prefix = ''

        if message.startswith('[') and ']:' in message:
            context, message = message.split(']:', 1)
            if context!=self.__context.get(logger, None):
                context_prefix = (
                        f'--{context}]\n'
                        f'{" " * (self.__indent+16)}'
                        )
                self.__context[logger] = context

        message = f'  {"  " * self.__indent}{message}'

        message = f'\n{self.blank_column}'.join(textwrap.wrap(
                message,
                width = WRAP_WIDTH,
                subsequent_indent = (
                    '  \\   ' + ' ' * self.__indent),
                ))

        result = (
                f'{logger:4}{level_letter} {module:6}'
                f'{record.lineno:5}{" " * self.__indent}'
                f'{context_prefix}{message}'
                )

        if temporary_indent:
            self.__indent -= 1

        return result

getLogger = Loggers.getLogger
selectLoggers = Loggers.selectLoggers

__all__ = [
        'LOGGERS',
        'DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL',
        'getLogger',
        'selectLoggers',
        ] + list(MAGIC)
