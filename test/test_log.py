import mex.log
import mex.state
import logging
from itertools import chain

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
    s = mex.state.State()

    for name in ['tracing'+x for x in LOGNAMES]:
        assert s.controls[name] is not None

def test_log_tracingonline(capsys, tmp_path):
    logfile = tmp_path / "mex.log"

    logger = logging.getLogger('mex.macros')
    s = mex.state.State()
    s.controls['tracingonline'].logging_filename = logfile.absolute()

    s.controls['tracingmacros'].value = 1
    s.controls['tracingonline'].value = 0
    logger.info('I like cheese')

    s.controls['tracingonline'].value = 1
    logger.info('So do I')
    assert logfile.read_text().strip() == "I like cheese"
    assert capsys.readouterr().out.strip() == "So do I"

def test_log_variables(capsys):

    names = LOGNAMES
    names.remove('online')

    s = mex.state.State()
    s.controls['tracingonline'].value = 1

    for i in names:
        for j in names:
            for level in (0, 1, 2):
                if i==j:
                    s.controls['tracing'+j].value = level
                else:
                    s.controls['tracing'+j].value = 0

                logger = logging.getLogger("mex."+j)
                logger.info("info %d %s", level, i)
                logger.debug("debug %d %s", level, i)

    expected = list(chain.from_iterable([
            (
                f"info 1 {name}",
                f"info 2 {name}",
                f"debug 2 {name}",
                )
            for name in names]))
    found = capsys.readouterr().out.strip().split('\n')
    
    assert expected == found
