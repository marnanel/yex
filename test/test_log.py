import yex.control.log
import yex.document
import logging
import pytest
from itertools import chain

# It's important to del your Document before attempting to
# read capsys.readouterr(), because that will close sys.stdout,
# and Document will want to do some debug logging before it closes.

yex.control.logger = logging.getLogger('yex')

@pytest.fixture(autouse=True)
def ensure_logging_framework_not_altered():
    """
    Resets the handlers on yex.control.logger after a test.
    See https://github.com/pytest-dev/pytest/issues/5743 for why.
    """
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

def test_log_names():
    s = yex.document.Document()

    for name in [fr'\tracing{x}' for x in LOGNAMES]:
        assert s.controls[name] is not None

def test_log_tracingonline(capsys, tmp_path):

    def _only_stars(s):
        s = s.strip().split('\n')
        return ''.join([
            x[1:] for x in s
            if x.startswith('*')])

    logfile = tmp_path / "yex.control.log"

    logger = logging.getLogger('yex.macros')
    s = yex.document.Document()
    s.controls.contents[
            r'\tracingonline'].logging_filename = logfile.absolute()

    s.controls[r'\tracingmacros'] = 1
    s.controls[r'\tracingonline'] = 0
    logger.info('*I like cheese')

    s.controls[r'\tracingonline'] = 1
    logger.info('*So do I')

    del s

    assert _only_stars(logfile.read_text()) == "I like cheese"
    assert _only_stars(capsys.readouterr().out) == "So do I"

def test_log_variables(capsys):

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
