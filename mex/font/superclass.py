import mex.value
import logging

commands_logger = logging.getLogger('mex.commands')

class Font:
    def __init__(self,
            tokens = None,
            filename = None,
            scale = None,
            name = None,
            state = None,
            ):

        if state is not None:
            self.hyphenchar = state['defaulthyphenchar']
            self.skewchar = state['defaultskewchar']
        else:
            self.hyphenchar = ord('-')
            self.skewchar = -1

        self._metrics = None
        self.has_been_used = False

    def __getitem__(self, n):

        if not isinstance(n, int):
            raise TypeError()
        if n<=0:
            raise ValueError()

        if n in self.metrics.dimens:
            result = mex.value.Dimen(self.metrics.dimens[n])
        else:
            result = mex.value.Dimen()

        commands_logger.debug(
                r"%s: lookup dimen %s, == %s",
                self, n, result)

        return result

    def __setitem__(self, n, v):
        if not isinstance(n, int):
            raise TypeError()
        if n<=0:
            raise ValueError()
        if not isinstance(v, mex.value.Dimen):
            raise TypeError()

        if n not in self.metrics.dimens and self.has_been_used:
            raise mex.exception.MexError(
                    "You can only add new dimens to a font "
                    "before you use it.")

        commands_logger.debug(
                r"%s: set dimen %s, = %s",
                self, n, v)
        self.metrics.dimens[n] = v

    def _set_from_tokens(self, tokens):
        raise NotImplementedError()
