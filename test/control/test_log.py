import yex.control.keyword.trace
import yex.document
import logging
import pytest
from itertools import chain

# It's important to del your Document before attempting to
# read capsys.readouterr(), because that will close sys.stdout,
# and Document will want to do some debug logging before it closes.

yex.control.logger = logging.getLogger('yex')

@pytest.fixture(autouse=True)
def logging_tests(caplog):
    """
    Sets logging to CRITICAL to avoid spamming the user.

    Also, resets the handlers on yex.control.logger after a test.
    See https://github.com/pytest-dev/pytest/issues/5743 for why.
    Remove that part when the issue is fixed.
    """

    caplog.set_level(logging.CRITICAL)
    before_handlers = list(yex.control.logger.handlers)

    yield
    yex.control.logger.handlers = before_handlers

LOGNAMES = [
            'online',
            'macros',
            'stats',
            'paragraphs',
            'pages',
            'output',
            'lostchars',
            'commands',
            'restores',
            ]

@pytest.mark.xfail
def test_control_log_variables(capsys):

    names = LOGNAMES
    names.remove('online')

    s = yex.document.Document()
    s.controls[r'\tracingonline'] = 1

    for i in names:
        for j in names:
            for level in (0, 1, 2):
                if i==j:
                    s.controls[fr'\tracing{j}'] = level
                else:
                    s.controls[fr'\tracing{j}'] = 0

                logger = logging.getLogger("yex."+j)
                logger.info("*info %d %s", level, i)
                logger.debug("*debug %d %s", level, i)

    del s

    expected = list(chain.from_iterable([
            (
                f"info 1 {name}",
                f"info 2 {name}",
                f"debug 2 {name}",
                )
            for name in names]))
    found = [x[1:] for x in
            capsys.readouterr().out.strip().split('\n')
            if x.startswith('*')]

    assert expected == found
