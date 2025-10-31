r"""
Yex's logging facilities.

Note:
    Logging is in a state of flux. This may be obsolescent
    by the time you read this.

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

TeX logger keywords:
    At some point it might be useful to allow this mechanism
    to turn TeX's loggers on and off. (Their keywords would
    be found in `yex.control.keyword.log`.) This is the reason
    for the `internal` flag in LoggerKeyword.
"""
import logging as builtin_logging
from logging import DEBUG, INFO, WARN, WARNING, ERROR, CRITICAL
import sys
import os
import textwrap
from typing import List, Union, Self

ALL = 'all'
NONE = 'none'
LIST = 'list'
VERBOSE = 'verbose'

MAGIC = { ALL, NONE, LIST, VERBOSE }

DEFAULT = 'all'

ENVIRON_CHOOSE_LOGGERS = 'YEX_LOGGERS'
ENVIRON_NO_CATCH = 'YEX_LOG_NO_CATCH'

WRAP_WIDTH = 70

class LoggerKeyword:

    keywords = {}

    def __init__(self,
                 name:str,
                 help:str,
                 default:bool=False,
                 magic:bool=False,
                 internal:bool=True,
                 ):
        self.name = name
        self.help = help
        self.magic = magic
        self.default = default
        self.internal = internal

    def __repr__(self):
        def yes(b, s):
            if b:
                return s
            return ' '*len(s)

        result = (
                    f'{self.name:10s} '
                    f'{yes(self.default, "d")} '
                    f'{yes(self.internal, "i")} '
                    f'{yes(self.magic, "--")} '
                    f'{self.help}'
                    )
        return self.name

    def builtin_logger(self) -> builtin_logging.Logger:
        if self.magic:
            raise ValueError(
                    f"{self.name} is magic, so you can't get a handle on it.")
        elif self.internal:
            result = builtin_logging.getLogger(f'yex.general.{self.name}')
        else:
            # see "TeX logger keywords" in this module's docstring
            raise ValueError(
                    "TeX-based logger; not sure how to proceed")

        return result

    @classmethod
    def register_keywords(self, keywords:List[Self]):
        self.keywords |= dict([
            (v.name, v) for v in keywords
            ])

class PositionLoggerKeyword(LoggerKeyword):
    def __init__(self):
        super().__init__(
            name = 'position',
            help = 'where we currently are in the source',
            default = True,
            )
        class _NoSource:
            tail = ''
        self.source = _NoSource()
        self.depth = 0
        self.depths_used = [False]
        self.logger = self.builtin_logger()

    def report(self, s):
        self.logger.info("%11s:%*s%s",
                         self.source.tail,
                         self.depth*4,
                         '',
                         s)
        self.depths_used[-1] = True
        return self

    def indent(self):
        if self.depths_used[-1]:
            self.depth += 1

        self.depths_used.append(False)

    def dedent(self):
        self.depths_used.pop()
        if self.depths_used[-1]:
            self.depth -= 1

    def __enter__(self):
        self.indent()
        return self

    def __exit__(self, type, value, traceback):
        self.dedent()

position_logger = PositionLoggerKeyword()

LoggerKeyword.register_keywords(
        [
            LoggerKeyword(
                name = 'general',
                help = 'anything not otherwise covered',
                default = True,
                ),
            LoggerKeyword(
                name = 'parser',
                help = 'parsing (spammy)',
                default = False,
                ),
            LoggerKeyword(
                name = 'control',
                help = 'what controls are running',
                default = False,
                ),
            LoggerKeyword(
                name = 'output',
                help = 'how we\'re producing output',
                default = False,
                ),
            LoggerKeyword(
                name = 'exception',
                help = 'errors',
                default = False,
                ),
            LoggerKeyword(
                name = 'value',
                help = 'numbers, dimensions, and so on',
                default = False,
                ),
            LoggerKeyword(
                name = 'parse',
                help = 'the parser',
                default = False,
                ),
            LoggerKeyword(
                name = 'tokeniser',
                help = 'reading, character by character',
                default = False,
                ),
            LoggerKeyword(
                name = 'expander',
                help = 'parsing',
                default = False,
                ),
            LoggerKeyword(
                name = 'box',
                help = 'constructing boxes on the page',
                default = False,
                ),
            LoggerKeyword(
                name = 'mode',
                help = 'horizontal, vertical, or maths layout',
                default = False,
                ),
            LoggerKeyword(
                name = 'font',
                help = 'letter shapes and metrics',
                default = False,
                ),
            LoggerKeyword(
                name = 'filename',
                help = 'filenames',
                default = False,
                ),
            LoggerKeyword(
                name = 'io',
                help = 'input and output streams',
                default = False,
                ),
            LoggerKeyword(
                name = 'document',
                help = 'what gets stored and looked up',
                default = False,
                ),
            LoggerKeyword(
                name = 'test',
                help = 'details of tests, for developers',
                default = False,
                ),
            position_logger,
            LoggerKeyword(
                name = 'main',
                help = 'the main program (wrapping everything else)',
                default = False,
                ),
            LoggerKeyword(
                name = 'wrap',
                help = 'end-of-page wordwrap calculations',
                default = False,
                ),

            LoggerKeyword(
                name = ALL,
                help = 'turn them all on',
                magic = True,
                ),
            LoggerKeyword(
                name = NONE,
                help = 'turn them all off',
                magic = True,
                ),
            LoggerKeyword(
                name = LIST,
                help = 'show all the names (and then stop)',
                magic = True,
                ),
            LoggerKeyword(
                name = VERBOSE,
                help = 'show extremely spammy debug logs',
                magic = True,
                ),
        ])


class Loggers:

    @classmethod
    def list_text(cls):

        result = (
                "You should supply a comma-separated list of logger names,\n"
                "either using -l or --loggers, or failing those, using\n"
                f"the {ENVIRON_CHOOSE_PARSERS} environment variable.\n"
                "\n"
                "The possibilities are:\n"
                )

        for keyword in sorted(LoggerKeyword.keywords.keys()):
            result += f'  {keyword}\n'

        result += (
                "\n"
                "Options marked 'd' are defaults "
                "if you don't specify anything.\n"
                "Options marked 'i' are internal to yex; the others are "
                "TeX builtins.\n"
                )
        return result

    @classmethod
    def selectLoggers(cls,
                      handlers: str,
                      ) -> None:
        """
        Sets the loglevel of all loggers.

        This behaves as described in this module's docstring.

        Note that "turning a logger off" means setting its
        loglevel to WARNING, and "turning a logger on" means
        setting its level to DEBUG if "verbose" is off, and
        INFO otherwise.

        Args:
            handlers: a comma-separated list of handlers;
                see this module's docstring for details of the format.
                If this is `None`, we will look in the environment
                variable given by `ENVIRON_CHOOSE_LOGGERS`.
        """
        builtin_logger = builtin_logging.getLogger('yex')

        # TODO how much of this do we need to do if we're inside a test?

        # Remove existing handlers. (Test harnesses will leave them in.)
        for handler in builtin_logger.handlers:
            builtin_logger.removeHandler(handler)

        stream_handler = builtin_logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(MainLoggingFormatter())

        builtin_logger.addHandler(stream_handler)

        if not handlers:
            try:
                handlers = os.environ[ENVIRON_CHOOSE_LOGGERS]
                source = f'environment variable {ENVIRON_CHOOSE_LOGGERS}'
            except KeyError:
                handlers = DEFAULT
                source = 'default'
        else:
            source = 'command line'

        requested = set(handlers.split(','))

        unknown = requested - LoggerKeyword.keywords.keys()

        if unknown:
            print("yex: these names are unknown:")
            print("yex:   " + ' '.join(sorted(unknown)))
            print(f"yex: (from {source})")
            print("yex: For a list, do '--loggers list'.")
            sys.exit(254)

        if LIST in requested:
            print(self.list_text())
            sys.exit(255)

        if NONE in requested:
            requested.remove(NONE)

        verbose = VERBOSE in requested
        if verbose:
            requested.remove(VERBOSE)

        if ALL in requested:
            requested = LoggerKeyword.keywords.keys() - MAGIC - requested

        for name, handler in sorted(LoggerKeyword.keywords.items()):

            if handler.magic:
                continue

            sublogger = handler.builtin_logger()
            if name not in requested:
                sublogger.setLevel(WARNING)
            elif verbose:
                sublogger.setLevel(DEBUG)
            else:
                sublogger.setLevel(INFO)

    @classmethod
    def getLogger(cls, name:str):
        r"""
        Gets the yex logger with the given name.

        Args:
            name: the name of the logger. That is,
                `yex.logger.` plus the given string

        Raises:
            ValueError: if name refers to a "magic" logger,
                like `"all"`
            KeyError: if the logger requested is unknown
        """
        result = LoggerKeyword.keywords[name].builtin_logger()

        return result

class MainLoggingFormatter(builtin_logging.Formatter):

    blank_column = ' ' * 14

    def __init__(self):
        super().__init__()
        self.__indent = 0
        self.__context = {}

    def format(self, record):
        try:
            return self._inner_format(record)
        except Exception as e:
            if os.environ.get(ENVIRON_NO_CATCH, '')=='1':
                raise

            return (
                    f'Exception during logging: {e}\n'
                    f'  Record was: {record}\n'
                    'To allow this exception through, '
                    f'set {ENVIRON_NO_CATCH}=1.'
                    )

    def _inner_format(self, record):
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
