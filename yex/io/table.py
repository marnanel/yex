import os
import yex
import logging

logger = logging.getLogger('yex.general')

class StreamsTable:
    def __init__(self, doc, our_type):
        self.streams = {}
        self.doc = doc
        self.our_type = our_type
        self.is_queryable = False
        self.is_array = True

    def open(self, number, filename):

        if number>=0 and number<=15:
            try:

                if number in self.streams:
                    if self.streams[number].f is not None:
                        logger.debug("%s: nb: opening new stream over: %s",
                                self, self.streams[number])

                if filename is None:
                    result = self.our_type.on_terminal(
                            doc=self.doc,
                            number=number,
                            )
                    logger.debug("%s: opened %s = terminal",
                            self, number)

                else:
                    result = self.our_type(
                            filename=filename,
                            number=number,
                            doc=self.doc,
                            )
                    logger.debug("%s: opened %s = %s",
                            self, number, repr(filename))

                self.streams[number] = result
            except OSError as ose:
                logger.info(
                        "%s: open of %s = %s failed: %s",
                        self,
                        number,
                        repr(filename),
                        ose,
                        )

            return self.streams[number]

        logger.debug("%s: opened %s = terminal",
                self, number)
        return self.our_type.on_terminal(doc=self.doc, number=number)

    def close(self, number):
        """
        Closes a stream.

        If there is no stream with the given number, does nothing.

        Args:
            number: the number of the stream to close.
        """
        if number not in self.streams:
            logger.debug(("%s: can't close stream %s which we don't have; "
                "doing nothing"),
                self, number)
            return

        logger.debug('%s: closing stream %s (currently %s)',
                self, number, self.streams[number])

        self.streams[number]._actually_close()
        del self.streams[number]

    def get_element(self, index):

        if index<0 or index>15:
            logger.debug("%s: returning terminal for stream number %s",
                self, index)
            return self.our_type.on_terminal(doc=self.doc, number=index)

        if index not in self.streams:
            logger.debug('%s: no stream %s; returning terminal',
                self, index)
            return self.open(number=index, filename=None)

        return self.streams[index]

    def __str__(self):
        return f'{self.our_type.__name__} table'
