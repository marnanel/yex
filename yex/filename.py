import logging
import os
import glob
import yex
import appdirs

logger = logging.getLogger('yex.general')

APPNAME = 'yex'

class Filename(str):
    """
    The name of a file on disk.

    This can just be a filename. But if you call resolve(),
    it will attempt to find you an existing file with that name.
    """

    def __new__(cls,
            name,
            default_extension = 'tex',
            ):
        if not isinstance(name, str):
            raise ValueError(
                    f"name must be a string "
                    f"(and not {name}, which is a {type(name)}")

        if default_extension is not None:
            name = cls._maybe_add_extension(name=name,
                    default_extension = default_extension,
                    )

        result = super().__new__(cls, name)
        return result

    @classmethod
    def _maybe_add_extension(cls,
            name,
            default_extension,
            ):
        _, existing_extension = os.path.splitext(name)

        if existing_extension=='' and default_extension is not None:
            if not default_extension.startswith('.'):
                name += '.'
            name += default_extension

        return name

    @property
    def name(self):
        return self

    def resolve(self):
        """
        Attempts to find an existing file with the given name.

        If one is found, we return a new Filename with the
        absolute path.

        If one is not found, we raise FileNotFoundError.

        Raises:
            FileNotFoundError: if there is no such file.

        Returns:
            Filename
        """

        cls = self.__class__

        def _exists(name):
            if os.path.exists(name):
                logger.debug(f"    -- %s exists", name)
                return os.path.abspath(name)
            else:
                logger.debug(f"    -- %s does not exist", name)
                return None

        logger.debug(f"Searching for {self.name}...")

        if os.path.isabs(self.name):

            path = _exists(self.name)

            if path is not None:
                logger.debug("  -- absolute path, exists")
                return cls(path,
                        default_extension = None,
                        )

            logger.debug("  -- absolute path, does not exist")
            raise FileNotFoundError(self)

        in_current_dir = _exists(os.path.abspath(self.name))
        if in_current_dir is not None:
            logger.debug("  -- exists in current directory")
            return cls(in_current_dir,
                    default_extension = None,
                    )

        config_dirs = [
                appdirs.user_data_dir(appname=APPNAME),
                appdirs.site_data_dir(appname=APPNAME),
        ]

        for config_dir in config_dirs:

            path = _exists(
                    os.path.join(
                        config_dir,
                        self.name))

            if path is not None:
                logger.debug("    -- exists in %s", path)
                return cls(path,
                    default_extension = None,
                        )

        logger.debug("  -- can't find it")
        raise FileNotFoundError(self)

    @property
    def abspath(self):
        """
        Returns our absolute path.

        (We may not currently exist, so this file may not currently exist
        either.)

        Returns:
            Filename
        """
        return self.__class__(os.path.abspath(self),
                default_extension = None,
                )

    def __eq__(self, other):
        if hasattr(other, 'value'):
            other = other.value

        return super().__eq__(other)

    @property
    def basename(self):
        """
        The name of the file, without any path and without any extension.

        For example, "/usr/share/wombat.pdf" returns "wombat".

        Returns:
            str (not Filename)
        """
        root, _ = os.path.splitext(self.name)
        result = os.path.basename(root)

        return result


    @classmethod
    def from_tokens(cls, tokens,
            default_extension = 'tex',
            ):
        """
        Reads a filename from a token stream.

        Filenames must consist only of Letter and Other tokens.

        Args:
            tokens (Expander): the stream to read the filename from
            default_extension (str or None): the extension to add
                if the filename has no extension. If it doesn't begin
                with a dot, a dot is added anyway. If it's None,
                no extension will be added.

        Raises:
            ParseError if there isn't a filename to be found.
        """

        logger.debug("Setting filename from tokens")

        tokens.eat_optional_spaces()
        name = ''

        for token in tokens.another(level='reading'):
            if isinstance(token, (yex.parse.Letter, yex.parse.Other)):
                name += token.ch
            else:
                tokens.push(token)
                break

        if name=='':
            raise yex.exception.ParseError("I needed a filename here.")

        if default_extension:
            name = cls._maybe_add_extension(name, default_extension)

        result = cls(name,
                default_extension = None,
                )
        logger.debug('Filename found: %s', result)
        return result
