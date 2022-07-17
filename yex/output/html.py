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
PIXELS_PER_SP = (72*65536)/96 # exactly 49152

class Html(Output):

    filename_extension = 'html'

    def __init__(self,
            doc,
            filename):

        self.doc = doc
        self.filename = filename
        self.responsive = None

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

        for thing in self.doc.contents:
            if isinstance(thing, yex.box.VBox) and self.responsive:
                self.responsive.add(vbox=thing)
            else:
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

    def _handle_box(self, item, html_container, depth):
        new_block = self.result.new_tag('span')
        new_block['yex:type'] = 'box'

        style = (
                'display:inline-block;'
                f'width:{px(item.width)};'
                f'height:{px(item.height)};'
                )

        new_block['style'] = style

        html_container.append(new_block)

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

    def _handle_whatsit(self, item, html_container, depth):
        result = item()

        if result is None:
            return
        elif result=='html.responsive.start':
            if self.responsive is not None:
                raise yex.exception.YexError(
                        "Responsive block has already started")

            self.responsive = Responsive(doc=self.doc)

        elif result=='html.responsive.again':
            if self.responsive is None:
                raise yex.exception.YexError(
                        "Not in a responsive block")

            self.responsive.again()

        elif result=='html.responsive.done':
            if self.responsive is None:
                raise yex.exception.YexError(
                        "Not in a responsive block")

            self.responsive.finish()
            self.responsive = None

        elif result.startswith('html.'):

            raise yex.exception.YexError(
                    f"Unknown HTML special: {result}")

        else:
            logger.debug("html: ignoring special that isn't for us: %s",
                    result)

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
    if isinstance(width, yex.value.Dimen):
        width = width.value
    return '%.3gpx' % (width/PIXELS_PER_SP,)

class Responsive:
    def __init__(self, doc):
        self.doc = doc
        self.contents = []
        self.widths = []

    def add(self, vbox):

        hsize = max([n.width.value for n in vbox.contents])

        self.widths.append(hsize)

        ritems = ResponsiveItem.from_vbox(
                parent=self,
                vbox=vbox,
                hsize=hsize,
                )

        if not self.contents:
            for item in ritems:
                self.contents.append(item)
            logger.debug("RI: added initial contents")
            return

        header_line = 'LRM    '
        for w in sorted(self.widths):
            header_line += '%9s' % (px(w),)
        header_line += '; type     ; value'

        logger.debug('='*len(header_line))
        logger.debug(header_line)
        logger.debug('='*len(header_line))

        left_items = iter(self.contents)
        right_items = ritems

        sync = None

        result = []
        left = next(left_items)
        right = next(right_items)

        try:
            while True:

                left_index  = getattr(left.item,  'source_index', None)
                right_index = getattr(right.item, 'source_index', None)

                logger.debug('%3s     L   %s', left_index or '-', left)
                logger.debug('    %3s  R  %s',  right_index or '-', right)

                if left_index==right_index:
                    left.merge_with(right)
                    logger.debug('          M %s', left)
                    result.append(left)

                    left = next(left_items)
                    right = next(right_items)

                elif left_index is not None and right_index is not None:
                    raise ValueError("these paragraphs are too different")

                elif left_index is not None:
                    result.append(right)
                    logger.debug('         >  %s', right)
                    right = next(right_items)

                else:
                    result.append(left)
                    logger.debug('        <   %s', left)
                    left = next(left_items)

                logger.debug('---')

        except StopIteration:
            pass

        # any left?
        for left in left_items:
            logger.debug('        <   %s', left)
            result.append(left)

        for right in right_items:
            logger.debug('         >  %s', right)
            result.append(right)

        logger.debug('RI: ends  --- L=left, R=right (new), M=merged, <>=added')

        self.contents = result

    def again(self):
        logger.debug("--- again ---")

    def finish(self):
        logger.debug("--- finish ---")
        for i, item in enumerate(self.contents):
            logger.debug('%3s - %s', i, item)

class ResponsiveItem:
    def __init__(self, parent, hsize, item):
        self.parent = parent
        self.item = item
        self.widths = {}
        self.breaks = set()

        if isinstance(item, yex.box.Leader):
            self.widths[hsize] = item.space.value
        elif type(item)==yex.box.Box:
            self.widths[hsize] = item.width

    def __repr__(self):
        result = '[ri'

        for w in sorted(self.parent.widths):
            result += ';'

            if w in self.breaks:
                result += '*'
            else:
                result += ' '

            if w in self.widths:
                result += '%7s' % (px(self.widths[w]),)
            else:
                result += ' '*7

        result += ';%9s;%s' % (
                self.item.__class__.__name__[:7],
                repr(self.item),
                )

        for w in sorted(self.widths):
            if w not in self.parent.widths:
                logger.warn('%s: rogue width: %s',
                    self, w,
                    )

        for w in sorted(self.breaks):
            if w not in self.parent.widths:
                logger.warn('%s: rogue break: %s',
                    self, w,
                    )

        return result

    def merge_with(self, another):
        self.widths |= another.widths
        self.breaks |= another.breaks

        if not isinstance(another.item, type(self.item)):
            logger.warn('RI: disparate types in add: %s vs %s',
                    self.item.__class__.__name__,
                    another.item.__class__.__name__,
                    )
            raise ValueError()

    @classmethod
    def from_vbox(cls, parent, vbox, hsize):

        logger.info('RI: constructing at size %s from vbox: %s',
                hsize, vbox)
        for hbox in vbox.contents:
            last = len(hbox.contents)-1
            for i, item in enumerate(hbox.contents):

                found = ResponsiveItem(
                        parent = parent,
                        hsize = hsize,
                        item = item,
                        )

                if i==last:
                    found.breaks.add(hsize)

                yield found
