import io
import os
import yex.filename
import yex.parse
import yex.document
import logging
import appdirs

logger = logging.getLogger('yex.general')

def _build_fs(fs):

    for dirname in [
            appdirs.user_data_dir(appname=yex.filename.APPNAME),
            appdirs.site_data_dir(appname=yex.filename.APPNAME),
            ]:

        fs.create_dir(dirname)

    fs.cwd = '/home/user'

def _test_filename(
        name,
        as_literal,
        filetype = None,
        create_files = None,
        fs = None,
        monkeypatch = None,
        ):

    logger.debug(("===== Begin test for %s: as_literal=%s, filetype=%s, "
            "create_files = %s, fs = %s, monkeypatch = %s"),
            name,
            as_literal,
            filetype,
            create_files,
            fs,
            monkeypatch,
            )

    if as_literal:
        fn = yex.filename.Filename(
                name = name,
                default_extension = filetype,
                )
    else:
        tokens = yex.Document().open(name)
        fn = yex.filename.Filename.from_tokens(
                tokens = tokens,
                default_extension = filetype,
                )

    assert isinstance(fn, yex.filename.Filename)
    logger.debug("created Filename: %s", fn)

    if create_files:
        for name in create_files:
            fs.create_file(name)
            logger.debug("created file: %s", name)

    if monkeypatch:
        def _pretend_expanduser(path):
            if path.startswith('~/'):
                return '/home/user/'+path[2:]
            else:
                return path

        monkeypatch.setattr(os.path, 'expanduser',
                _pretend_expanduser)
        logger.debug("monkeypatched: %s", os.path.expanduser)
    return fn

def test_filename_from_string(fs):

    fn = _test_filename(
            name = 'wombat',
            as_literal = True,
            )

    assert fn=='wombat'
    assert str(fn)=='wombat'

def test_filename_with_filetype(fs):

    fn = _test_filename(
            name = 'wombat',
            as_literal = True,
            filetype = 'html',
            )

    assert fn=='wombat.html'
    assert str(fn)=='wombat.html'

def test_filename_path():

    fn = _test_filename(
            name = 'wombat',
            as_literal = True,
            )

    assert os.path.isabs(fn.abspath)
    assert fn.basename=='wombat'

def test_filename_with_dirs_path():

    fn = _test_filename(
            name = '/hello/world/wombat',
            as_literal = True,
            )

    assert fn=='/hello/world/wombat'
    assert fn.abspath == '/hello/world/wombat'
    assert fn.basename == 'wombat'

def test_filename_from_tokens():

    fn = _test_filename(
            name = r'wombat foo',
            as_literal = False,
            )

    assert fn == 'wombat'

def test_filename_from_tokens_with_filetype():

    fn = _test_filename(
            name = r'wombat foo',
            as_literal = False,
            filetype = 'txt',
            )

    assert fn == 'wombat.txt'

def test_filename_resolve_simple(fs):

    _build_fs(fs)

    app_dirname = appdirs.user_data_dir(appname=yex.filename.APPNAME)
    if not app_dirname:
        raise ValueError("no user data dir is defined")

    filename_in_appdir = os.path.join(app_dirname, 'wombat')
    fn = _test_filename(
            name = 'wombat',
            fs = fs,
            as_literal = True,
            create_files = [
                filename_in_appdir,
                ],
            )

    assert fn == 'wombat'

    resolved = fn.resolve()
    assert resolved == filename_in_appdir

    fn = _test_filename(
            name = 'wombat',
            as_literal = True,
            create_files = [
                '/home/user/wombat.tfm',
                ],
            fs = fs,
            )

    assert fn == 'wombat'
    resolved = fn.resolve()
    assert resolved == filename_in_appdir
