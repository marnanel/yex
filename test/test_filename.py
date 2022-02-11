import io
import os
import mex.filename
import mex.token
import mex.state

def _build_fs(fs):
    for dirname in [
            '/usr/share/gnome/mex',
            '/home/user/.fonts',
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

    if not as_literal:
        s = mex.state.State()
        f = io.StringIO(name)
        name = mex.token.Tokeniser(
                state = s,
                source = f,
                )

    if create_files:
        for name in create_files:
            fs.create_file(name)

    if monkeypatch:
        def _pretend_expanduser(path):
            if path.startswith('~/'):
                return '/home/user/'+path[2:]
            else:
                return path

        monkeypatch.setattr(os.path, 'expanduser',
                _pretend_expanduser)

    fn = mex.filename.Filename(
            name = name,
            filetype = filetype,
            )

    return fn

def test_filename_from_string(fs):

    fn = _test_filename(
            name = 'wombat',
            as_literal = True,
            )

    assert fn.value=='wombat'

def test_filename_path():

    fn = _test_filename(
            name = 'wombat',
            as_literal = True,
            )

    path = fn.path

    assert os.path.isabs(path[0])
    assert os.path.basename(path)=='wombat'

def test_filename_with_dirs_path():

    fn = _test_filename(
            name = '/hello/world/wombat',
            as_literal = True,
            )

    assert fn.path == '/hello/world/wombat'

def test_filename_from_tokens():

    fn = _test_filename(
            name = r'wombat foo',
            as_literal = False,
            )

    assert fn.value == 'wombat'

def test_filename_from_tokens_with_filetype():

    fn = _test_filename(
            name = r'wombat foo',
            as_literal = False,
            filetype = 'txt',
            )

    assert fn.value == 'wombat.txt'

def test_filename_from_tokens_with_filetype_font():

    fn = _test_filename(
            name = r'wombat foo',
            as_literal = False,
            filetype = 'font',
            )

    assert fn.value == 'wombat'

def test_filename_resolve_simple(fs):

    _build_fs(fs)

    fn = _test_filename(
            name = 'wombat',
            fs = fs,
            as_literal = True,
            create_files = [
                "/usr/share/gnome/mex/wombat",
                ],
            )

    fn.resolve()
    path = fn.path

    assert path == '/usr/share/gnome/mex/wombat'

def test_filename_resolve_font(fs,
        monkeypatch):

    _build_fs(fs)

    for filename, works in [
                ("/home/user/.local/share/mex/wombat.tfm", True),
                ("/home/user/.fonts/wombat.ttf", True),
                ("/home/user/untitled-goose-game", False),
            ]:

        fn = _test_filename(
                name = 'wombat',
                fs = fs,
                monkeypatch = monkeypatch,
                as_literal = True,
                create_files = [
                    filename,
                    ],
                filetype = 'font',
                )

        fn = mex.filename.Filename(
                name = 'wombat',
                filetype = 'font',
                )

        try:
            fn.resolve()
            path = fn.path
        except FileNotFoundError:
            path = None

        if works:
            assert path == filename
        else:
            assert path == None

        fs.remove_object(filename)
