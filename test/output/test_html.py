import tempfile
from test import *
import os
import yex

def _html_driver(
        code = None,
        filename = 'wombat.html',
        ):

    # If you're not saving the document, it doesn't matter
    # what filename you use
    doc = yex.Document()

    if code is not None:
        run_code(code, doc=doc)

    result = yex.output.html.Html(doc, filename)

    return result

def test_output_html_init():
    h = _html_driver()

    # h.result is BeautifulSoup

    assert h.result.find('title').string=='Yex output'

def test_output_html_can_handle():
    assert yex.output.html.Html.can_handle('html')
    assert yex.output.html.Html.can_handle('htm')
    assert not yex.output.html.Html.can_handle('pdf')

def test_output_html_render():

    output_dir = tempfile.mkdtemp(prefix='yex-test')
    filename = os.path.join(
            output_dir,
            'wombat.html')

    h = _html_driver("Where have all the flowers gone?",
            filename)

    h.render()

    assert False
