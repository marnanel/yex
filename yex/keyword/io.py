"""
Input/output controls.

These deal with access to files and streams.
"""
import yex.logging
from yex.control.control import Unexpandable
import yex.exception
import yex.value
import yex.io

logger = yex.logging.getLogger('control')

@yex.decorator.control()
def Immediate(parser):

    t = parser.next(level='querying', on_eof='raise')

    logger.debug(r'\immediate: got %s', t)
    if not isinstance(t, yex.box.Whatsit):
        logger.debug(r'\immediate: found %s: not really our problem',
                t)
        return

    logger.debug(r'\immediate: calling %s', t)

    t()

    logger.debug(r'\immediate: calling %s: done', t)

@yex.decorator.control()
def Openin(stream_id: int, parser):
    parser.eat_optional_char('=')
    parser.eat_optional_spaces()

    filename = yex.filename.Filename.from_parser(parser,
            default_extension = 'tex')

    parser.doc[f'_inputs'].open(
            number = stream_id,
            filename = filename,
            )

@yex.decorator.control()
def Openout(stream_id: int, parser):
    parser.eat_optional_char('=')
    parser.eat_optional_spaces()

    filename = yex.filename.Filename.from_parser(parser,
            default_extension = 'tex')

    class Opener(yex.box.Whatsit):
        def render(self):
            parser.doc[f'_outputs'].open(
                    number = stream_id,
                    filename = filename,
                    )

    result = Opener()

    return result

@yex.decorator.control()
def Closein(stream_id: int, parser):
    parser.doc[f'_inputs;{stream_id}'].close()

@yex.decorator.control()
def Closeout(stream_id: int, parser):
    parser.doc[f'_outputs;{stream_id}'].close()

@yex.decorator.control(
        even_if_not_expanding = True,
        )
def Write(stream_id: int, parser):

    if not parser.is_expanding:
        logger.debug("%s: not doing anything, because we're not expanding",
                self)
        return None

    parser.eat_optional_char('=')

    # ...then the tokens to print.

    nesting = 0
    message = []

    for token in parser.another(
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

            stream = parser.doc[f'_outputs;{stream_id}']
            contents = parser.another(
                    source=message,
                    level='expanding',
                    on_eof='exhaust',
                    )

            buf = ''

            for t in contents:
                if isinstance(t, yex.control.Register):
                    # Idk why, but this is what TeX does
                    buf += f'\\{t.array.name} {t.index}'
                else:
                    buf += str(t)

            stream.write(buf)

        def __repr__(self):
            return f'[{self.__class__.__name__};{message}]'

    result = Writer()

    return result

@yex.decorator.control()
def Read(stream_id:int, where:yex.parse.Location, parser):
    parser.eat_optional_spaces()

    if not parser.optional_string('to'):
        # not all that optional, then is it?
        raise yex.exception.NeededToHere()

    parser.eat_optional_spaces()

    target_symbol = parser.next(level='deep', on_eof='raise')

    logger.debug(r"\read: reading from input stream %s into %s...",
            stream_id, target_symbol)

    new_value = parser.doc[f'_inputs;{stream_id}'].read(
            varname = target_symbol,
            )

    logger.debug(r"\read: found: %s", repr(new_value))

    if new_value is None:
        new_value = []

    new_macro = yex.control.Macro(
            doc = parser.doc,
            definition = new_value,
            parameter_text = [],
            starts_at = where,
            )
    logger.debug(r"\read: created new macro: %s", new_macro)

    parser.doc[target_symbol.identifier] = new_macro
    logger.debug(r"\read: and assigned it to %s.", target_symbol.ch)
