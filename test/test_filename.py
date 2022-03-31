import io
import os
import yex.filename
import yex.parse
import yex.document

def _build_fs(fs):
    for dirname in [
            '/usr/share/gnome/yex',
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
        name = yex.document.Document().open(name)

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

    fn = yex.filename.Filename(
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
                "/usr/share/gnome/yex/wombat",
                ],
            )

    fn.resolve()
    path = fn.path

    assert path == '/usr/share/gnome/yex/wombat'

def test_filename_resolve_font(fs,
        monkeypatch):

    _build_fs(fs)

    for filename, realtype, works in [
                ("/home/user/.local/share/yex/wombat.tfm", 'tfm', True),
                ("/home/user/.fonts/wombat.ttf", 'ttf', True),
                ("/home/user/untitled-goose-game", None, False),
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

        fn = yex.filename.Filename(
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
            assert fn.filetype == realtype
        else:
            assert path == None

        fs.remove_object(filename)

def test_basename(fs):
    fn = _test_filename(
            name = 'wombat',
            as_literal = True,
            create_files = [
                '/home/user/wombat.tfm',
                ],
            fs = fs,
            )

    assert fn.basename == 'wombat'
