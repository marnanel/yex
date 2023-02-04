import io
import yex.document
import yex.parse
import yex.exception
import yex.output
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

def put(source = None,
        doc = None,
        catch = True,
        target = None,
        target_format = None,
        dump = False,
        dump_full = False,
        ):
    """
    Puts a string, or the contents of a file, into a Document.

    Args:
        source (str, file-like, or None): code to pass into the Document
        doc (Document or None): the document. If this is None,
            we will create a Document for the occasion.
        catch (bool): if True, we will catch exceptions from the Document
            during processing, and turn them into PutErrors with
            the current file position. If False, we pass exceptions
            straight through to our caller. Defaults to True.
        target (str, Output, or None): where the Document should save
            its contents when we're finished. If this is a String,
            it's a filename; we construct an Output, whose file format is
            based on target_format, or failing that, the extension.
            If this is an Output, we use it as is.
            If this is None, the Document doesn't save.
        target_format (str, or None): the name of the format to use
            if we're constructing an Output. If this is None, we work it out
            from the filename extension.
        dump (bool): if True, we dump the contents of the Document as JSON
            to stdout when we're done, and don't save. Fields which are
            the same as at the start of processing aren't printed.
            Defaults to False, of course.
        dump_full (bool): like dump, except that we'll dump everything.
            Takes priority over dump.

    Returns:
        if "doc" was not None, the value of "doc". Otherwise, the Document
            we constructed and used instead.
    """

    if doc is None:
        doc = yex.document.Document()

    e = yex.parse.Expander(
            source,
            doc = doc,
            on_eof='exhaust',
            )

    if isinstance(target, yex.output.Output):
        doc['_output'] = target
    else:
        doc['_output'] = yex.output.Output.driver_for(
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

        if dump or dump_full:
            _dump_doc_contents(doc, dump_full)
        elif target:
            doc.save()

    except Exception as exception:
        if not catch:
            raise

        message = f'{exception.__class__.__name__} {exception}'
        context = t.error_position(message)

        raise PutError(
                message = message,
                context = context,
                )

    return doc

def _dump_doc_contents(doc, full):

    import json

    value = doc.__getstate__(full)

    print(json.dumps(
        value,
        indent=2,
        sort_keys=True,
        default=_get_getstate,
        ))

def _get_getstate(value):

    try:
        values_ajf = getattr(value, '__getstate__')
    except AttributeError:
        raise TypeError(
                f'json encoding sent us {value}, of type {type(value)}, '
                f'which doesn\'t have an __getstate__() method')

    try:
        result = values_ajf()
    except:
        raise TypeError(
                f'json encoding sent us {value}, of type {type(value)}, '
                f'whose __getstate__() is '
                f'{values_ajf}, of type {type(values_ajf)}, '
                f'rather than something we can use.'
                )

    return result
