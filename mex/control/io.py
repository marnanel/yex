import logging
from mex.control.word import C_ControlWord
from mex.control.string import C_StringControl
import mex.exception

general_logger = logging.getLogger('mex.general')

class Immediate(C_ControlWord):

    def __call__(self,
            name,
            tokens):

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

        handler.expect_immediate()

        tokens.push(t)

class Openout(C_StringControl):
    def __call__(self,
            name,
            tokens,
            ):

        if not running:
            return

        raise NotImplementedError()

    def expect_immediate(self):
        pass

class Closeout(C_ControlWord):
    def __call__(self,
            name,
            tokens,
            ):
        if not running:
            return

        raise NotImplementedError()

    def expect_immediate(self):
        pass

class Write(C_StringControl):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.immediate = False

    def expect_immediate(self):
        self.immediate = True

    def __call__(self, name, tokens,
            running = True):

        result = []

        for t in mex.parse.Expander(
                tokens=tokens,
                single=True,
                running=False):

            if running:
                raise NotImplementedError()
            else:
                result.append(t)

        self.immediate = False

        return result
