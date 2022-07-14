import logging
import copy
import collections
import base64
import io
import string
import os
import importlib.resources
import yex
from yex.output import Output
from bs4 import BeautifulSoup

logger = logging.getLogger('yex.general')

# W3C mandates that 96px==1in in printed output.
PIXELS_TO_SP = (72*65536)/96 # exactly 49152

class Html(Output):

    filename_extension = 'html'

    def __init__(self,
            doc,
            filename):

        self.doc = doc
        self.filename = filename

        with (importlib.resources.files(
                yex) / "res" / "output" / "html" / "base.html"
                ).open('r') as base:
            self.result = BeautifulSoup(base,
            features="lxml",
                    )

        logger.debug("html: loaded base from base.html")

    @classmethod
    def can_handle(cls, file_extension):
        return file_extension in ['html', 'htm']

    def render(self):

        main_block = self.result.find(role='main')

        # Who<u class="r" style="width: 20px;">
        # main_block.append(str(thing))

        for thing in self.doc.contents:
            self._handle(thing, main_block, depth=0)

        self._write_out()

    def _handle(self, item, html_container, depth):

        logger.debug("html: %*srendering: %s", depth, '', item)

        handler_name = '_handle_'+item.__class__.__name__.lower()

        handler = getattr(self, handler_name, None)

        if handler is None:
            raise ValueError(
                    f"Don't know how to handle {item.__class__.__name__}")

        handler(item, html_container, depth)

    def _handle_vbox(self, item, html_container, depth):
        new_block = self.result.new_tag('p')
        new_block['yex:type'] = 'vbox'
        html_container.append(new_block)

        for thing in item.contents:
            self._handle(thing, new_block, depth+1)

    def _handle_hbox(self, item, html_container, depth):
        new_block = self.result.new_tag('span')
        new_block['yex:type'] = 'hbox'
        html_container.append(new_block)

        for thing in item.contents:
            self._handle(thing, new_block, depth+1)

    def _handle_wordbox(self, item, html_container, depth):
        word = self.result.new_tag('span')
        word['class'] = 'word'
        word['style'] = 'max-width: '+str(item.width)
        word.append(item.ch)

        html_container.append(word)

    def _handle_leader(self, item, html_container, depth):
        spacer = self.result.new_tag('u')
        spacer['class'] = 'b'
        spacer['style'] = 'width: '+str(item.space)
        spacer.append('\n') # some actual whitespace, in case of no CSS

        html_container.append(spacer)

    def _handle_discretionarybreak(self, item, html_container, depth):
        pass

    def _handle_penalty(self, item, html_container, depth):
        pass

    def _write_out(self):
        logger.debug("html: writing to %s", self.filename)
        with open(self.filename, 'w') as out:
            out.write(str(self.result))

        base_dir = os.path.dirname(self.filename)
        for extra in [
                'cmr10.ttf',
                ]:
            logger.debug("html: copying %s", self.filename)
            with (importlib.resources.files(
                    yex) / "res" / "output" / "html" / extra
                    ).open('rb') as f:
                content = f.read()

            with open(
                    os.path.join(base_dir, extra), 'wb') as f:
                f.write(content)

        logger.debug("html: done!")

def px(width):
    return '%gpx' % (width.value/PIXELS_PER_SP,)
