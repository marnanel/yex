import logging
import os
import glob
import appdirs
import fclist

macros_logger = logging.getLogger('mex.macros')

APPNAME = 'mex'
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
            self.value = name
            return

        self.tokens = name
        self.value = ''

        self.tokens.eat_optional_spaces()

        for c in self.tokens:
            if c and c.category in (c.LETTER, c.OTHER):
                macros_logger.debug("filename character: %s",
                        c)
                self.value += c.ch
            else:
                self.tokens.push(c)
                break

        if self.value=='':
            raise ValueError("no filename found")

        if '.' not in self.value and self.filetype is not None \
                and self.filetype!='font':
            self.value = f"{self.value}.{self.filetype}"

        macros_logger.debug("Filename is: %s", self.value)

    def resolve(self):
        """
        Attempts to find an existing file with the given name.
        If one is found, self.path will return that name.
        If one is not found, we raise FileNotFoundError.

        If this method has already been called on this object,
        it returns immediately.
        """

        def _exists(name):
            """
            If self.filetype is "font", checks all files matching
            "{name}.*" looking for a font, returning the full path if
            one exists and None if one doesn't.

            Otherwise, returns the full path if "name" exists,
            and None if it doesn't.
            """
            if self.filetype!='font':
                if os.path.exists(name):
                    macros_logger.debug(f"    -- %s exists", name)
                    return os.path.abspath(name)
                else:
                    macros_logger.debug(f"    -- %s does not exist", name)
                    return None

            candidates = glob.glob(name+'*')
            macros_logger.debug("    -- is there a font called %s?", name)
            macros_logger.debug('with %s', list(candidates))
            for maybe_font in candidates:
                root, ext = os.path.splitext(maybe_font)

                if ext[1:].lower() in FONT_TYPES:

                    macros_logger.debug("        -- yes, of type %s",
                            ext)
                    head, tail = os.path.split(name)
                    return os.path.join(head, maybe_font)
                else:
                    macros_logger.debug(f"      -- %s is not a font type",
                            ext)

            macros_logger.debug(f"        -- no")
            return None

        macros_logger.debug(f"Searching for {self.value}...")
        if self._path is not None:
            macros_logger.debug("  -- already found; returning")

        if os.path.isabs(self.value):

            path = _exists(self.value)

            if path is not None:
                macros_logger.debug("  -- absolute path, exists")
                self._path = path
                return

            macros_logger.debug("  -- absolute path, does not exist")
            raise FileNotFoundError(self.value)

        in_current_dir = _exists(os.path.abspath(self.value))
        if in_current_dir is not None:
            macros_logger.debug("  -- exists in current directory")
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
                        self.value))

            if path is not None:
                macros_logger.debug("    -- exists in %s", path)
                self._path = path
                return

        if self.filetype=='font':
            name = self.value.replace('_', ' ')
            candidates = fclist.fclist(family=self.value)

            for candidate in candidates:
                # TODO probably we want to choose a particular one
                macros_logger.debug("  -- installed font found, called %s",
                        candidate)

                return candidate.file
            else:
                macros_logger.debug("  -- no installed font called %s",
                        name)

        macros_logger.debug("  -- can't find it")
        raise FileNotFoundError(self.value)

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

        return os.path.abspath(self.value)

    def __str__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value==other
        else:
            return self.value==other.value
