class Output:
    """
    A driver which can write a Document to disk, in a given file format.
    """

    def __init__(self,
            doc,
            filename):
        self.doc = doc
        self.filename = filename

    def render(self):
        """
        Writes the document out to disk.

        The document and filename were given to this object's constructor
        earlier.

        Once you have called this argument, don't call it again.

        This is an abstract method: override it in all subclasses.
        """
        raise NotImplementedError()

    @classmethod
    def can_handle(cls, format):
        """
        Whether this driver can handle files of this format.

        This is an abstract method: override it in all subclasses.

        Args:
            format (str): the kind of file we'll be writing to.
                This is always a possible extension for that file format.
                Examples might be "pdf" or "html".
                Use all lowercase, and omit the leading dot.
        """
        raise NotImplementedError()

    @classmethod
    def driver_for(cls, doc, filename, format=None):
        """
        Creates an instance of an output driver.

        Args:
            doc (yex.Document): the current Document; this is passed through
                to the new driver
            filename (str): the name of the file we'll be writing to
            format (str, optional): the name of the file format; if this
                is omitted or None, we take the filename extension.

        Returns:
            an instance of one of Output's subclasses, instantiated to
                write the given Document to the given filename.
        """

        import os, yex, logging, inspect

        logger = logging.getLogger('yex.general')

        logger.debug(
                ('Output.driver_for: looking up output driver for '
                    'filename=%s, format=%s'),
                filename, format)

        if filename is None:
            result = yex.output.Null(doc=doc, filename=filename)
            logger.debug('  -- returning null output driver: %s',
                    result)
            return result

        if format is None:
            _, format = os.path.splitext(filename)

            if format.startswith('.'):
                format = format[1:]

            logger.debug('  -- deducing format from filename: %s', format)

        logger.debug('  -- asking all drivers about their capability')
        def _can_handle_it(driver_class):
            logger.debug('    -- can %s handle %s?', driver_class, format)

            result = driver_class.can_handle(format)
            if result:
                logger.debug('      -- yes')
            else:
                logger.debug('      -- no')

            return result


        capable = [
            driver for name, driver in inspect.getmembers(yex.output)
            if driver.__class__==type and
            issubclass(driver, cls)
            and driver!=cls
            and _can_handle_it(driver)
            ]

        logger.debug('  -- found: %s', capable)

        if len(capable)==0:
            logger.debug('  -- %s is unknown; bail', format)
            raise yex.exception.WeirdFormatError(
                    format = format,
                    )
        elif len(capable)>1:
            logger.debug('  -- warning the user that there are several')
            print(f'warning: there are multiple drivers which '
                    f'can handle {format}:',
                ', '.join([x.__class__.__name__ for x in capable]),
                '-- using ',capable[0].__class__.__name__,
                    )

        result = capable[0](
                doc = doc,
                filename = filename,
                )

        logger.debug('  -- result: %s', result)
        return result

    def __repr__(self):
        result = f'[{self.__class__.__name__.lower()} output driver'

        try:
            result += f';filename={self.filename}'
        except AttributeError:
            pass

        result += ']'
        return result
