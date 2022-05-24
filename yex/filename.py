import logging
import os
import glob
import appdirs
import yex.parse

logger = logging.getLogger('yex.general')

APPNAME = 'yex'
FONT_TYPES = ['tfm', 'ttf', 'otf']

class Filename:
    """
    The name of a file on disk.
    """

    def __init__(self,
            name,
            filetype = None,
            ):
        """
        "name" can be a string, in which case it's the
        name of the file, or a Tokenstream, in which case
        the name of the file is read from it.

        "filetype" is the extension of the file we're
        looking for, or "none" for no extension.
        If it's "font", it will match any font we can
        handle.

        If the filename is read from tokens, and it
        doesn't contain a dot, and "filetype" is not None
        and not "font", then a dot and "filetype" are
        appended to the name.
        """

        self.filetype = filetype
        self._path = None

        if isinstance(name, str):
            self.tokens = None
            self._filename = name
            return

        logger.debug("Setting filename from tokens")
        self.tokens = name
        self._filename = ''

        self.tokens.eat_optional_spaces()

        for c in self.tokens.another(level='reading'):
            if isinstance(c, yex.parse.Token) and \
                    c.category in (c.LETTER, c.OTHER):
                logger.debug("filename character: %s",
                        c)
                self._filename += c.ch
            else:
                self.tokens.push(c)
                break

        if self._filename=='':
            raise ValueError("no filename found")

        if '.' not in self._filename and self.filetype is not None \
                and self.filetype!='font':
            self._filename = f"{self._filename}.{self.filetype}"

        logger.debug("Filename is: %s", self._filename)

    def resolve(self):
        """
        Attempts to find an existing file with the given name.
        If one is found, self.path will contain that name.
        If one is not found, we raise FileNotFoundError.

        If this method has already been called on this object,
        it returns immediately.
        """

        def _exists(name):
            """
            If self.filetype is "font", checks all files matching
            "{name}.*" looking for a font, returning the full path if
            one exists and None if one doesn't. If one exists,
            also sets self.filetype to the file extension as a
            side-effect. (XXX Not elegant.)

            Otherwise, returns the full path if "name" exists,
            and None if it doesn't.
            """
            if self.filetype!='font':
                if os.path.exists(name):
                    logger.debug(f"    -- %s exists", name)
                    return os.path.abspath(name)
                else:
                    logger.debug(f"    -- %s does not exist", name)
                    return None

            candidates = glob.glob(name+'*')
            logger.debug("    -- is there a font called %s?", name)
            logger.debug('with %s', list(candidates))
            for maybe_font in candidates:
                root, ext = os.path.splitext(maybe_font)

                if ext[1:].lower() in FONT_TYPES:

                    logger.debug("        -- yes, of type %s",
                            ext)
                    self.filetype = ext[1:]
                    head, tail = os.path.split(name)
                    return os.path.join(head, maybe_font)
                else:
                    logger.debug(f"      -- %s is not a font type",
                            ext)

            logger.debug(f"        -- no")
            return None

        logger.debug(f"Searching for {self._filename}...")
        if self._path is not None:
            logger.debug("  -- already found; returning")

        if os.path.isabs(self._filename):

            path = _exists(self._filename)

            if path is not None:
                logger.debug("  -- absolute path, exists")
                self._path = path
                return

            logger.debug("  -- absolute path, does not exist")
            raise FileNotFoundError(self._filename)

        in_current_dir = _exists(os.path.abspath(self._filename))
        if in_current_dir is not None:
            logger.debug("  -- exists in current directory")
            self._path = in_current_dir
            return

        for config_dir in [
                appdirs.user_data_dir(appname=APPNAME),
                appdirs.site_data_dir(appname=APPNAME),
                os.path.expanduser('~/.fonts'),
                ]:

            path = _exists(
                    os.path.join(
                        config_dir,
                        self._filename))

            if path is not None:
                logger.debug("    -- exists in %s", path)
                self._path = path
                return

        logger.debug("  -- can't find it")
        raise FileNotFoundError(self._filename)

    @property
    def path(self):
        """
        Returns an absolute path. If resolve() has been called,
        the path returned will always be the path resolve() found.
        If not, we return a path for the given filename in
        the current directory. This file may not currently exist.
        """
        if self._path is not None:
            return self._path

        return os.path.abspath(self._filename)

    def __str__(self):
        return self.value

    @property
    def value(self):
        """
        The name of this file.

        If we have run `resolve()`, this is the same as the return value
        of `resolve()`. Otherwise, it's the filename value given to
        our constructor.
        """
        if self._path:
            return self._path
        else:
            return self._filename

    def __eq__(self, other):
        if isinstance(other, str):
            return self._filename==other
        else:
            return self._filename==other.value

    @property
    def basename(self):
        """
        The name of the file, without any path and without any extension.

        For example, "/usr/share/fonts/wombat.tfm" returns "wombat".

        Result:
            `str`
        """
        root, _ = os.path.splitext(self._filename)
        result = os.path.basename(root)

        return result
