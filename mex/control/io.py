import logging
from mex.control.word import *
from mex.control.string import C_StringControl
import mex.exception
import mex.value

general_logger = logging.getLogger('mex.general')
macros_logger = logging.getLogger('mex.macros')

class Immediate(C_Expandable):

    def __call__(self,
            name,
            tokens):

        t = tokens.next()

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

class C_IOControl(C_StringControl):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.immediate = False

    def expect_immediate(self):
        self.immediate = True

class Openout(C_IOControl):
    def __call__(self,
            name,
            tokens,
            ):

        if not expand:
            return

        raise NotImplementedError()

class Closeout(C_IOControl):
    def __call__(self,
            name,
            tokens,
            ):
        if not expand:
            return

        raise NotImplementedError()

# XXX TODO This is wrong and needs rewriting

class Write(C_IOControl):
    def __call__(self, name, tokens,
            expand = True):

        e = tokens.single_shot(
                expand=False)

        was_immediate = self.immediate

        self.immediate = False

        if expand:
            stream_number = mex.value.Number(tokens)

            self.do_write(name, e,
                    stream_number = stream_number,
                    immediate = was_immediate)
        else:
            return self.pass_through(name, e)

    def do_write(self, name, e, stream_number, immediate):

        macros_logger.debug(
                "writing to stream %s",
                stream_number)

        contents = [t for t in e]

        # TODO On printing, "contents" should be evaluated
        # with expand=True. Possibly whatever's handling
        # the streams can do that for us when we're sending
        # log messages too.

        if stream_number<0 or stream_number>15:
            # This might need its own special logger

            macros_logger.info(
                    "Log message: %s",
                    contents)
        else:
            macros_logger.critical(
                    "writing to stream %s: %s",
                    stream_number, contents)
            raise NotImplementedError()

    def pass_through(self, name, e):
        result = [t for t in e]
        result.insert(0, name)
        return result
