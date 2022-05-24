"""
Input/output controls.

These deal with access to files and streams.
"""
import logging
from yex.control.control import *
from yex.control.string import C_StringControl
import yex.exception
import yex.value
import yex.io

logger = logging.getLogger('yex.general')

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

class Immediate(C_Unexpandable):

    def __call__(self, tokens):

        t = tokens.next()

        logger.debug("%s: the next item is %s",
                self, t)

        if isinstance(t, yex.box.Whatsit):
            # \write will already have run. It's handled specially
            # because its arguments are read without expansion
            # (hence its inheritance from C_StringControl).
            whatsit = t

        elif isinstance(t, C_IOControl):
            whatsit = t(tokens)

        else:
            raise yex.exception.ParseError(
                    r"\immediate must be followed by an I/O control, "
                    f"and not {t}"
                    )

        logger.debug("%s: %s: calling it",
               self, whatsit)

        whatsit()

        logger.debug("%s: %s: finished calling it",
               self, whatsit)

class C_IOControl(C_Unexpandable):
    pass

class Openin(C_IOControl):
    pass

class Openout(C_IOControl):
    def __call__(self,
            tokens,
            ):

        raise NotImplementedError()

class Closein(C_IOControl):
    pass

class Closeout(C_IOControl):
    pass

class Write(C_StringControl):

    # This inherits from C_StringControl to give a clue about
    # how to handle it; it doesn't rely on code from the superclass.

    def __call__(self,
            tokens,
            expand = False,
            ):

        if not expand:
            logger.debug("%s: not doing anything, because expand=False",
                    self)
            return None

        # Stream number first...
        stream_number = yex.value.Number(tokens)
        logger.debug("%s: stream number is %s",
                self, stream_number)

        tokens.eat_optional_equals()

        # ...then the tokens to print.
        message = [t for t in
            tokens.another(
                single=True,
                on_eof='exhaust',
                level='reading',
                )]

        logger.debug("%s: will probably get around to "
                "writing to %s saying %s",
                self, stream_number, message)

        whatsit = yex.box.Whatsit(
                on_box_render = lambda: self.do_write(
                    stream_number = stream_number,
                    message = message,
                    tokens = tokens,
                    ),
                )

        tokens.push(whatsit)

    def do_write(self, stream_number, message, tokens):

        class Governor(yex.parse.Internal):
            def __init__(self):
                super().__init__()
                self.write_is_running = True

            def __call__(self, *args, **kwargs):
                logger.debug(
                        "%s: finished writing to stream %s saying %s",
                        self, stream_number, message)

                self.write_is_running = False

        logger.debug(
                "%s: writing to stream %s saying %s",
                self, stream_number, message)

        stream = tokens.doc[f'_output;{stream_number}']
        governor = Governor()

        # pushing back, so in reverse
        tokens.push(governor)
        tokens.push(message)

        while governor.write_is_running:
            t = tokens.next(
                    level='expanding',
                    )

            if hasattr(t, '__call__'):
                t(tokens)
            else:
                stream.write(str(t))

class Input(C_IOControl): pass
class Endinput(C_IOControl): pass
class Read(C_IOControl): pass
