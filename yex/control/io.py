"""
Input/output controls.

These deal with access to files and streams.
"""
import logging
from yex.control.control import *
import yex.exception
import yex.value
import yex.io

logger = logging.getLogger('yex.general')

class Immediate(C_Unexpandable):

    def __call__(self, tokens):

        t = tokens.next()

        logger.debug("%s: the next item is %s",
                self, t)

        if isinstance(t, yex.box.Whatsit):
            # \write will already have run. It's handled specially
            # because its arguments are read without expansion
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

@yex.decorator.control()
def Openin(stream_id: int, tokens):
    tokens.eat_optional_equals()
    tokens.eat_optional_spaces()

    filename = yex.filename.Filename.from_tokens(tokens,
            default_extension = 'tex')

    tokens.doc[f'_inputs'].open(
            number = stream_id,
            filename = filename,
            )

@yex.decorator.control()
def Openout(stream_id: int, tokens):
    tokens.eat_optional_equals()
    tokens.eat_optional_spaces()

    filename = yex.filename.Filename.from_tokens(tokens,
            default_extension = 'tex')

    def do_open():
        tokens.doc[f'_outputs'].open(
                number = stream_id,
                filename = filename,
                )

    result = yex.box.Whatsit(
        on_box_render = do_open,
        )

    return result

@yex.decorator.control()
def Closein(stream_id: int, tokens):
    tokens.doc[f'_inputs;{stream_id}'].close()

@yex.decorator.control()
def Closeout(stream_id: int, tokens):
    tokens.doc[f'_outputs;{stream_id}'].close()

@yex.decorator.control(
        even_if_not_expanding = True,
        )
def Write(stream_id: int, tokens):

    if not tokens.is_expanding:
        logger.debug("%s: not doing anything, because we're not expanding",
                self)
        return None

    tokens.eat_optional_equals()

    # ...then the tokens to print.
    message = [t for t in
        tokens.another(
            single=True,
            on_eof='exhaust',
            level='reading',
            )]

    logger.debug(r"\write: will probably get around to "
            "writing to %s saying %s",
            stream_id, message)

    def do_write():

        class Governor(yex.parse.Internal):
            def __init__(self):
                super().__init__()
                self.write_is_running = True

            def __call__(self, *args, **kwargs):
                logger.debug(
                        r"\write: finished writing to stream %s saying %s",
                        stream_id, message)

                self.write_is_running = False

        logger.debug(
                r"\write: writing to stream %s saying %s",
                stream_id, message)

        stream = tokens.doc[f'_outputs;{stream_id}']
        governor = Governor()

        # pushing back, so in reverse
        tokens.push(governor, is_result = True)
        tokens.push(message, is_result = True)

        while governor.write_is_running:
            t = tokens.next(
                    level='expanding',
                    )

            if not governor.write_is_running:
                pass
            elif hasattr(t, '__call__'):
                t(tokens)
            else:
                stream.write(str(t))

    whatsit = yex.box.Whatsit(
            on_box_render = do_write,
            )

    return whatsit

class Input(C_IOControl): pass
class Endinput(C_IOControl): pass

@yex.decorator.control()
def Read(stream_id:int, where:yex.parse.Location, tokens):
    tokens.eat_optional_spaces()

    if not tokens.optional_string('to'):
        # not all that optional, then is it?
        raise yex.exception.ParseError('Needed "to" here')

    tokens.eat_optional_spaces()

    target_symbol = tokens.next(level='deep', on_eof='raise')

    logger.debug(r"\read: reading from input stream %s into %s...",
            stream_id, target_symbol)

    new_value = tokens.doc[f'_inputs;{stream_id}'].read(
            varname = target_symbol,
            )

    logger.debug(r"\read: found: %s", repr(new_value))

    if new_value is None:
        new_value = []

    new_macro = yex.control.C_Macro(
            definition = new_value,
            parameter_text = [],
            starts_at = where,
            )
    logger.debug(r"\read: created new macro: %s", new_macro)

    tokens.doc[target_symbol.ch] = new_macro
    logger.debug(r"\read: and assigned it to %s.", target_symbol.ch)
