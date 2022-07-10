import yex
from test import *

def test_get_driver_for():

    doc = yex.Document()

    def run(filename, format, expected_class):
        found = yex.output.get_driver_for(doc=doc,
                filename=filename,
                format=format,
                )

        context = f'{filename} {format}'

        assert isinstance(found, expected_class), context
        assert found.doc==doc, context

    # FIXME: these are fairly boring because we only have one output driver.
    # FIXME: when issue #61 or #62 is fixed, and we have an HTML or PDF
    #        driver, diversify them.

    run(filename=None, format=None,
            expected_class=yex.output.DEFAULT_DRIVER)

    run(filename='wombat.svg', format=None,
            expected_class=yex.output.Svg)

    run(filename='wombat.html', format=yex.output.Svg,
            expected_class=yex.output.Svg)

    instance = yex.output.Svg(doc=doc, filename='spong.svg')
    run(filename=None, format=instance,
            expected_class=yex.output.Svg)
