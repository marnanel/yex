import os
import sys
import logging

PARSER_LOGGING_ENV = 'YEX_LOGGERS'

class LoggerKeyword:
    def __init__(self, name, doc, default, internal=True):
        self.name = name
        self.doc = doc
        self.default = default
        self.internal = internal

    def __repr__(self):
        return f'[{self.name}]'

    @classmethod
    def get_valid_keywords(self):
        result = dict([
            (v.name, v) for v in INTERNAL_LOGGER_KEYWORDS
            ])

        # TODO add TeX keywords from yex.control.keyword.log
        return result

    @classmethod
    def help_text(cls):

        def yes(b, s):
            if b:
                return s
            return ' '*len(s)

        result = (
                "You should supply a comma-separated list of logger names,\n"
                "either using -l or --loggers, or failing those, using\n"
                f"the {PARSER_LOGGING_ENV} environment variable.\n"
                "\n"
                "The possibilities are:\n"
                )

        for k,v in sorted(cls.get_valid_keywords().items()):
            result += (
                    f'    {k:10s} '
                    f'{yes(v.default, "d")}{yes(v.internal, "y")} '
                    f'{v.doc}\n'
                    )

        result += (
                "    all        -- to turn them all on\n"
                "    none       -- to turn them all off\n"
                "    help       -- to show all the names (and stop)\n"
                "\n"
                "Options marked 'd' are defaults "
                "if you don't specify anything.\n"
                "Options marked 'y' are internal to yex; the others are "
                "TeX builtins.\n"
                "Supplying any value implies the verbosity is at least 1.\n"
                )
        return result

INTERNAL_LOGGER_KEYWORDS = {
        LoggerKeyword(
            name = 'general',
            doc = "anything not otherwise covered",
            default = True,
            ),
        LoggerKeyword(
            name = 'parser',
            doc = "parsing (spammy)",
            default = False,
            ),
        LoggerKeyword(
            name = 'wrap',
            doc = "end-of-page wordwrap calculations",
            default = False,
            ),
        }

def set_logging_levels(keywords=None,
                       verbosity=0):

    if keywords is None:
        keywords = os.environ.get(
                PARSER_LOGGING_ENV,
                None)

    valid = LoggerKeyword.get_valid_keywords()

    if keywords=='help':
        # I know it's not really an exceptional condition,
        # but many things use this function that would get
        # confused if everything stopped
        raise ValueError(LoggerKeyword.help_text())
    elif keywords is None:
        keywords = [v for k,v in valid.items()
                    if v.default]
    elif keywords=='all':
        keywords = valid.values()
    elif keywords=='none':
        keywords = []
    else:
        verbosity = max(verbosity, 1)
        keywords = keywords.split(',')
        unknown = set(keywords) - set(valid.keys())

        if unknown:
            raise ValueError(
                    f"You gave some logger names which were unknown:\n"
                    f"    {' '.join(sorted(unknown))}\n"
                    f'Use "-l help" to see a list of valid keywords.\n'
                    )

    for logger in valid.values():
        if logger.name in keywords:
            if verbosity==0:
                logging_level = logging.WARNING
            elif verbosity==1:
                logging_level = logging.INFO
            else:
                logging_level = logging.DEBUG
        else:
            logging_level = logging.WARNING

        logging.getLogger(f'yex.{logger.name}').setLevel(
                logging_level)

__all__ = [
        'set_logging_levels',
        ]
