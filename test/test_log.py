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

FORMATTING_TESTS = [
        (
            'Turkey trots to water',
            'par   test_l  Turkey trots to water',
            ),

        (
            (
                'The suburb of Saffron Park lay on the sunset side of London, '
                'as red and ragged as a cloud of sunset. It was built of a bright '
                'brick throughout; its sky-line was fantastic, and even its '
                'ground plan was wild. It had been the outburst of a speculative '
                'builder, faintly tinged with art, who called its architecture '
                'sometimes Elizabethan and sometimes Queen Anne, apparently under '
                'the impression that the two sovereigns were identical. It was '
                'described with some justice as an artistic colony, though it '
                'never in any definable way produced any art. But although its '
                'pretensions to be an intellectual centre were a little vague, '
                'its pretensions to be a pleasant place were quite indisputable.'
                ),

            (
                'fon   test_l  The suburb of Saffron Park lay on the sunset side of London, as red\n'
                '              and ragged as a cloud of sunset. It was built of a bright brick\n'
                '              throughout; its sky-line was fantastic, and even its ground plan was\n'
                '              wild. It had been the outburst of a speculative builder, faintly\n'
                '              tinged with art, who called its architecture sometimes Elizabethan and\n'
                '              sometimes Queen Anne, apparently under the impression that the two\n'
                '              sovereigns were identical. It was described with some justice as an\n'
                '              artistic colony, though it never in any definable way produced any\n'
                '              art. But although its pretensions to be an intellectual centre were a\n'
                '              little vague, its pretensions to be a pleasant place were quite\n'
                '              indisputable.'
                ),
            ),
        ]
def test_log_formatting(caplog):

    caplog.set_level(builtin_logging.DEBUG)
    yex.logging.selectLoggers('parse,font,verbose')
    builtin_logging.getLogger('yex').handlers = [] # do not spam stdout

    yex.logging.getLogger('parse').debug(
        FORMATTING_TESTS[0][0],
        )
    yex.logging.getLogger('font').debug(
        FORMATTING_TESTS[1][0],
        )

    formatter = yex.logging.MainLoggingFormatter()

    def remove_line_number(s):
        number_maybe = s[14:17].strip()
        assert number_maybe=='' or int(number_maybe)
        s = s[:12] + s[17:]
        return s

    for expected, record in zip(FORMATTING_TESTS, caplog.records):
        formatted = remove_line_number(formatter.format(record))
        with open('/tmp/aa', 'w') as f:
            f.write(formatted)
        assert formatted == expected[1]
