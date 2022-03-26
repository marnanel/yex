import logging
from yex.control.word import *
from yex.control.string import C_StringControl
import yex.exception
import yex.value
import yex.io

general_logger = logging.getLogger('yex.general')
macros_logger = logging.getLogger('yex.macros')

class X__Input(C_Not_for_calling):
    """
    This is where the input streams live.
    """
    def __init__(self):
        super().__init__()
        self._inputs = {}

    def __getitem__(self, n):
        if n>=0 and n<=15:
            if n in self._inputs:
                return self._inputs[n]

            # not open; return stream at EOF
            return yex.io.InputStream(f=None)
        else:
            return yex.io.TerminalInput(
                    show_variable_names = n>0,
                    )

class X__Output(C_Not_for_calling):
    """
    This is where the output streams live.
    """
    def __init__(self):
        super().__init__()
        self._outputs = {}

    def __getitem__(self, n):
        if n>=0 and n<=15:
            if n in self._outputs:
                return self._outputs[n]

            # not open; return stream at EOF,
            # though maybe we should warn or something
            return yex.io.OutputStream(f=None)
        else:
            return yex.io.TerminalOutput()

##############################
# FIXME Much of this is wrong. In particular, most of these operations
# should be put into box lists, and \immediate should cause them to
# run immediately.

class Immediate(C_Unexpandable):

    def __call__(self,
            name,
            tokens,
            ):

        t = tokens.next()

        macros_logger.debug("%s: the next token is %s",
                self, t)

        if t.category != t.CONTROL:
           macros_logger.debug("%s: not a control, so can't continue",
                   self, t)

           raise yex.exception.ParseError(
                    r"\immediate must be followed by a control, "
                    f"and not {t}"
                    )

        handler = tokens.doc[t.identifier]
        macros_logger.debug("%s: handler is %s",
               self, handler)

        handler(t, tokens)

class C_IOControl(C_Unexpandable):
    pass

class Openin(C_IOControl):
    pass

class Openout(C_IOControl):
    def __call__(self,
            name,
            tokens,
            ):

        if not expand:
            return

        raise NotImplementedError()

class Closein(C_IOControl):
    pass

class Closeout(C_IOControl):
    pass

# XXX TODO This is wrong and needs rewriting

class Write(C_IOControl):
    def __call__(self, name, tokens,
            expand = True):

        e = tokens.single_shot(
                expand=False)

        if expand:
            stream_number = yex.value.Number(tokens)

            self.do_write(name, e,
                    stream_number = stream_number)
        else:
            return self.pass_through(name, e)

    def do_write(self, name, e, stream_number):

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

class Input(C_IOControl): pass
class Endinput(C_IOControl): pass
class Read(C_IOControl): pass
