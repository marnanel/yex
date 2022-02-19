import mex.log
import mex.state
import logging
from itertools import chain

# It's important to del your State before attempting to
# read capsys.readouterr(), because that will close sys.stdout,
# and State will want to do some debug logging before it closes.

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

    def _only_stars(s):
        s = s.strip().split('\n')
        return ''.join([
            x[1:] for x in s
            if x.startswith('*')])

    logfile = tmp_path / "mex.log"

    logger = logging.getLogger('mex.macros')
    s = mex.state.State()
    s.controls.contents['tracingonline'].logging_filename = logfile.absolute()

    s.controls['tracingmacros'] = 1
    s.controls['tracingonline'] = 0
    logger.info('*I like cheese')

    s.controls['tracingonline'] = 1
    logger.info('*So do I')

    del s

    assert _only_stars(logfile.read_text()) == "I like cheese"
    assert _only_stars(capsys.readouterr().out) == "So do I"

def test_log_variables(capsys):

    names = LOGNAMES
    names.remove('online')

    s = mex.state.State()
    s.controls['tracingonline'] = 1

    for i in names:
        for j in names:
            for level in (0, 1, 2):
                if i==j:
                    s.controls['tracing'+j] = level
                else:
                    s.controls['tracing'+j] = 0

                logger = logging.getLogger("mex."+j)
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
