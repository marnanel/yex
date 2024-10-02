import logging as builtin_logging
import yex.logging
from yex.logging import DEBUG, INFO, WARNING
from test import *
import os

def test_log_settings():

    for case in [

            # Here we give the expected results of various
            # argument strings on three representative loggers.

            {'arg': 'all',
             'parse': 'INFO',
             'wrap': 'INFO',
             'font': 'INFO',
             },

            {'arg': 'none',
             'parse': 'WARNING',
             'wrap': 'WARNING',
             'font': 'WARNING',
             },

            {'arg': 'wrap',
             'parse': 'WARNING',
             'wrap': 'INFO',
             'font': 'WARNING',
             },

            {'arg': 'wrap,font',
             'parse': 'WARNING',
             'wrap': 'INFO',
             'font': 'INFO',
             },

            {'arg': 'all,wrap,font',
             'parse': 'INFO',
             'wrap': 'WARNING',
             'font': 'WARNING',
             },

            {'arg': 'verbose,wrap,font',
             'parse': 'WARNING',
             'wrap': 'DEBUG',
             'font': 'DEBUG',
             },
    ]:
        def test_the_levels(message):
            found = {
                    'arg': case['arg'],
                }
            for name in ['parse', 'wrap', 'font']:
                sublogger = builtin_logging.getLogger(
                        f'yex.general.{name}'
                        )

                found[name] = builtin_logging.getLevelName(
                        sublogger.level,
                        )

            assert found==case, message

        try:
            del os.environ['YEX_LOGGERS']
        except KeyError:
            pass

        yex.logging.selectLoggers(case['arg'])
        test_the_levels('commandline')

        os.environ['YEX_LOGGERS']=case['arg']
        yex.logging.selectLoggers(None)
        test_the_levels('environment')

        os.environ['YEX_LOGGERS']='nonsense'
        yex.logging.selectLoggers(case['arg'])
        test_the_levels('override')

    try:
        del os.environ['YEX_LOGGERS']
    except KeyError:
        pass

def test_log_invalid_logger_name():
    try:
        yex.logging.selectLoggers('nonsense')
        assert False, "invalid logger name was accepted"
    except SystemExit as se:
        assert se.code==254

def test_log_get_list(capsys):
    try:
        yex.logging.selectLoggers('list')
    except SystemExit as se:
        assert se.code==255

    assert capsys.readouterr().out=='\n'.join([
        f'  {n}' for n in [
            'all',
            'box',
            'control',
            'document',
            'expander',
            'filename',
            'font',
            'io',
            'list',
            'main',
            'mode',
            'none',
            'output',
            'parse',
            'test',
            'tokeniser',
            'value',
            'verbose',
            'wrap',
            ]]) + '\n'
