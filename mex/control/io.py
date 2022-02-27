import logging
from mex.control.string import C_StringControl
import mex.exception

general_logger = logging.getLogger('mex.general')

class Immediate(C_StringControl):

    def __call__(self,
            name,
            tokens,
            running = True):
        tokens.running = False
        for t in tokens:
            break
        tokens.running = True

        if t.category != t.CONTROL:
            raise mex.exception.ParseError(
                    r"\immediate must be followed by a control, "
                    f"and not {t}"
                    )

        if t.name not in [
                'openout',
                'closeout',
                'write',
                ]:
            raise mex.exception.ParseError(
                    r"\immediate can only be followed by 'openout', "
                    r"'close', or 'write', "
                    f"and not {t}"
                    )

        handler = tokens.state[t.name]

        return handler.__call__(t.name, tokens,
                immediate = True,
                running = running,
                )

class Openout(C_StringControl):
    def __call__(self,
            name,
            tokens,
            running = True,
            immediate = False,
            ):

        if not running:
            return

        raise NotImplementedError()

class Closeout(C_StringControl):
    def __call__(self,
            name,
            tokens,
            running = True,
            immediate = False,
            ):
        if not running:
            return

        raise NotImplementedError()

class Write(C_StringControl):
    def __call__(self,
            name,
            tokens,
            running = True,
            immediate = False,
            ):
        if not running:
            return

        raise NotImplementedError()
