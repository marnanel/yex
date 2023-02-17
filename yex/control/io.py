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

@yex.decorator.control()
def Immediate(tokens):

    t = tokens.next(level='querying', on_eof='raise')

    logger.debug(r'\immediate: got %s', t)
    if not isinstance(t, yex.box.Whatsit):
        logger.debug(r'\immediate: found %s: not really our problem',
                t)
        return

    logger.debug(r'\immediate: calling %s', t)

    t()

    logger.debug(r'\immediate: calling %s: done', t)

@yex.decorator.control()
def Openin(stream_id: int, tokens):
    tokens.eat_optional_char('=')
    tokens.eat_optional_spaces()

    filename = yex.filename.Filename.from_tokens(tokens,
            default_extension = 'tex')

    tokens.doc[f'_inputs'].open(
            number = stream_id,
            filename = filename,
            )

@yex.decorator.control()
def Openout(stream_id: int, tokens):
    tokens.eat_optional_char('=')
    tokens.eat_optional_spaces()

    filename = yex.filename.Filename.from_tokens(tokens,
            default_extension = 'tex')

    class Opener(yex.box.Whatsit):
        def render(self):
            tokens.doc[f'_outputs'].open(
                    number = stream_id,
                    filename = filename,
                    )

    result = Opener()

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

    tokens.eat_optional_char('=')

    # ...then the tokens to print.

    nesting = 0
    message = []

    for token in tokens.another(
            level = 'deep',
            on_eof = 'raise',
            ):

        message.append(token)

        if isinstance(token, yex.parse.BeginningGroup):
            nesting += 1
        elif isinstance(token, yex.parse.EndGroup):
            nesting -= 1

        if nesting==0:
            break

    if len(message)>1:
        message = message[1:-1]

    logger.debug(r"\write: will probably get around to "
            "writing to %s saying %s",
            stream_id, message)

    class Writer(yex.box.Whatsit):

        def render(self):
            logger.debug(
                    r"\write: writing to stream %s saying %s",
                    stream_id, message)

            stream = tokens.doc[f'_outputs;{stream_id}']
            contents = tokens.another(
                    source=message,
                    level='expanding',
                    on_eof='exhaust',
                    )

            buf = ''

            for t in contents:
                if isinstance(t, yex.control.C_Register):
                    # Idk why, but this is what TeX does
                    buf += f'\\{t.parent.name} {t.index}'
                else:
                    buf += str(t)

            stream.write(buf)

        def __repr__(self):
            return f'[{self.__class__.__name__};{message}]'

    result = Writer()

    return result

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
            doc = tokens.doc,
            definition = new_value,
            parameter_text = [],
            starts_at = where,
            )
    logger.debug(r"\read: created new macro: %s", new_macro)

    tokens.doc[target_symbol.ch] = new_macro
    logger.debug(r"\read: and assigned it to %s.", target_symbol.ch)
