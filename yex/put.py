import io
import yex.document
import yex.parse
import yex.exception
import argparse
import logging

logger = logging.getLogger('yex.general')

class PutError(Exception):
    def __init__(self,
            message,
            context):
        self.message = message
        self.context = context

    def __repr__(self):
        return self.context

    def __str__(self):
        return self.context

def put(source,
        doc = None,
        catch = True,
        target = None,
        target_format = None,
        ):

    if doc is None:
        doc = yex.document.Document()

    t = yex.parse.Tokeniser(
            doc = doc,
            source = source,
            )
    e = yex.parse.Expander(
            t,
            on_eof='exhaust',
            )

    output_driver = yex.output.get_driver_for(
            doc = doc,
            filename = target,
            format = target_format,
            )

    try:
        for item in e:
            logger.debug("  -- resulting in: %s", item)

            doc['_mode'].handle(
                    item=item,
                    tokens=e,
                    )

        if target:
            doc.save(target,
                    driver = output_driver,
                    )
        else:
            logger.warning("not saving because no filename given")

    except Exception as exception:
        if not catch:
            raise

        message = f'{exception.__class__.__name__} {exception}'
        context = t.error_position(message)

        raise PutError(
                message = message,
                context = context,
                )
