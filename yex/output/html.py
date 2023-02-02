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
SP_PER_PIXEL = (72*65536)/96 # exactly 49152

WIDTH_OF_MAIN_IN_SP = 350.0 * SP_PER_PIXEL

class Html(Output):

    filename_extension = 'html'

    def __init__(self,
            doc,
            filename):

        super().__init__(doc=doc, filename=filename)

        self.widths = [
                doc[r'\hsize'],
                ]

        self.current_line_lengths = [
                yex.value.Dimen(),
                ]

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

        self.main_block = self.result.find(role='main')
        self.responsive_para = None

        for page in self.doc.contents:
            for thing in page:
                self._handle(thing, self.main_block, depth=0)

        self._add_styles()
        self._write_out()

    @classmethod
    def _generate_written_words(cls, lines,
            merge_with = None,
            widths_version = None,
            ):

        logger.debug('html: generating written words from: %s',
                lines)
        result = []

        if merge_with:
            existing_iter = iter(merge_with)
            if widths_version is None:
                widths_version = len(merge_with[0].rhs)

        else:
            existing_iter = None
            widths_version = widths_version or 0

        for line in lines:
            logger.debug('  -- line: %s', line)

            if isinstance(line, yex.box.VBox):
                logger.debug('    -- is a VBox; recursing')
                result.extend(
                        cls._generate_written_words(line),
                        )
                continue
            elif not isinstance(line, yex.box.HBox):
                logger.debug('    -- which is not an HBox or VBox but a %s',
                        type(line))
                raise ValueError(
                        f'Expected an HBox or VBox but found {line} '
                        f'(which is a {type(line)}'
                        )

            lhs = 0

            for i, item in enumerate(line.contents):
                logger.debug('    -- item: %s', item)

                if isinstance(item, yex.box.Leader):

                    width = item.glue.space

                    if not result:
                        logger.debug('      -- this will be the first lhs')
                        lhs = width

                    else:
                        result[-1].rhs[widths_version] += width
                        logger.debug('      -- added to rhs of previous: %s',
                                result[-1])

                else:
                    if existing_iter is None:
                        result.append(WrittenWord(
                            lhs=lhs,
                            rhs=0,
                            word=item,
                            ))
                        logger.debug('      -- adding as new word: %s',
                                result[-1])

                    else:
                        result.append(next(existing_iter))
                        if result[-1].word.ch!=item.ch:
                            logger.error(('      -- existing and current '
                                'differ: old=%s, new=%s'),
                                    result[-1], item,
                                    )

                            raise ValueError((
                                    'Words differ in para merge; '
                                    'old=%s, new=%s. '
                                    'This is an error in '
                                    'your HTML stylesheet.') % (
                                    result[-1].word.ch, item.ch,
                                    ))

                        result[-1].lhs.append(lhs)
                        result[-1].rhs.append(0)

                        logger.debug('      -- merged with existing word: %s',
                                result[-1])

                    lhs = 0

            if result:
                if result[-1].rhs[widths_version]:
                    logger.debug(
                            '        -- replacing rhs of previous with break')
                else:
                    logger.debug(
                            '        -- setting rhs of previous to break')

                result[-1].rhs[widths_version] = None

        logger.debug('  -- done: %s', result)

        return result

    @classmethod
    def _generate_width_boxes(cls, items):
        result = []

        logger.debug('html: generating width boxes')

        for item in items:

            logger.debug('  -- item: %s', item)

            if not result:
                result.append(WidthBox())
                logger.debug('    -- added first width box')

            elif not result[-1].can_take(item):
                result.append(WidthBox())
                logger.debug('    -- doesn\'t fit; added new width box')

            result[-1] += item

        logger.debug('  -- done: %s', result)

        return result

    def _handle(self, item, html_container, depth):

        logger.debug("html: %20s %*srendering: %s",
                self.current_line_lengths, depth, '', item)

        handler_name = '_handle_'+item.__class__.__name__.lower()

        handler = getattr(self, handler_name, None)

        if handler is None:
            raise ValueError(
                    f"Don't know how to handle {item} "
                    f"(which is a {item.__class__.__name__})")

        handler(item, html_container, depth)

    def _handle_vbox(self, item, html_container, depth):
        new_block = self.result.new_tag('p')
        new_block['class'] = 'vbox'
        html_container.append(new_block)

        written_words = self._generate_written_words(item)

        width_boxes = self._generate_width_boxes(written_words)

        logger.debug("html: %*spopulating vbox: %s", depth, '', new_block)
        for width_box in width_boxes:
            html_width_box = self.result.new_tag('span')
            html_width_box['class'] = width_box.css_class
            new_block.append(html_width_box)

            logger.debug("html: %*spopulating width box: %s",
                    depth+1, '', html_width_box)

            for word in width_box:
                self._handle(word.word, html_width_box, depth+2)

            for eol in width_box.end_of_line_breaks(html=self):
                new_block.append(eol)

    def _handle_page(self, item, html_container, depth):
        self._handle_vbox(item, html_container, depth)

    def _handle_hbox(self, item, html_container, depth):
        new_block = self.result.new_tag('span')
        new_block['class'] = 'yex_hbox'
        html_container.append(new_block)

        for thing in item.contents:
            self._handle(thing, new_block, depth+1)

    def _handle_box(self, item, html_container, depth):
        new_block = self.result.new_tag('span')
        new_block['class'] = 'yex_box'

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

        self.current_line_lengths = [
                w+item.width for w in self.current_line_lengths]

        html_container.append(word)

    def _handle_leader(self, item, html_container, depth):
        return

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
            pass

        elif result=='html.responsive.again':
            pass

        elif result=='html.responsive.done':
            pass

        elif result.startswith('html.'):

            raise yex.exception.YexError(
                    f"Unknown HTML special: {result}")

        else:
            logger.debug("html: ignoring special that isn't for us: %s",
                    result)

    def _add_styles(self):

        style = ''
        DEBUG_COLOURS = ['red', 'green', 'yellow', 'blue', 'magenta',
                'cyan']

        for i, width in enumerate(self.widths):

            debug_colour = DEBUG_COLOURS[i%len(DEBUG_COLOURS)]

            if len(self.widths)>1:
                if i==0:
                    media_width = f'(max-width: {px(width)})'
                elif i+1==len(self.widths):
                    media_width = f'(min-width: {px(width)})'
                else:
                    media_width = (
                            f'(min-width: {px(width)}) and '
                            f'(max-width: {px(self.widths[i+1])})'
                            )

                style += fr'''
    @media {media_width} {{
                '''

        style += f'''
        body {{
            background-color: {debug_colour}
        }}

        br.b{i} {{
            display: inline-block;
        }}

{WidthBox.styles_for_all_classes(i)}
        '''

        style_tag = self.result.new_tag('style')
        style_tag.append(style)
        self.result.find('head').append(style_tag)

    def _write_out(self):
        logger.debug("html: writing to %s", self.filename)
        with open(self.filename, 'w') as out:
            out.write(str(self.result))

        base_dir = os.path.dirname(self.filename)
        for extra in [
                'cmr10.ttf',
                ]:
            logger.debug("html: copying %s", extra)
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
    return '%.3gpt' % (width/65536,)
    #return '%.3gpx' % (width/SP_PER_PIXEL,)

def _str_widths_for_repr(widths):
    result = []

    for w in widths:
        if w is None:
            s = 'br'
        else:
            s = str(w)
            if s.endswith('pt'):
                s = s[:-2]

        result.append(s)

    if not result:
        return 'empty'

    return ','.join(result)

class WrittenWord:
    def __init__(self, lhs=None, word=None, rhs=None):
        self.word = word
        self.lhs = [yex.value.Dimen()]
        self.rhs = [yex.value.Dimen()]

        if lhs:
            self.lhs[0] += lhs

        if rhs:
            self.rhs[0] += rhs

    @property
    def has_lhs(self):
        return [w for w in self.lhs if w] != []

    @property
    def contains_breaks(self):
        return [w for w in self.rhs if w is None] != []

    def matches_the_rhs_of(self, another):

        for a, b in zip(self.rhs, another.rhs):

            if a is None or b is None:
                continue

            if a!=b:
                return False

        return True

    def __repr__(self):
        result = '[ '

        if self.has_lhs:
            result += _str_widths_for_repr(self.lhs)
            result += ' '

        result += f'{self.word} '

        result += _str_widths_for_repr(self.rhs)

        result += ']'

        return result

class WidthBox:

    css_class_names = {}

    def __init__(self, html=None):
        self.contents = []
        self.full = False
        self.html = html

        self._css_class = None

    def can_take(self, item):

        if not self.contents:
            # we can always take an item if we're empty
            return True
        elif self.full:
            logger.debug('        -- already full')
            return False
        elif item.has_lhs:
            logger.debug('        -- needs a new box for its lhs')
            return False
        elif not self.contents[-1].matches_the_rhs_of(item):
            logger.debug('        -- doesn\'t match previous')
            return False

        return True

    def __iadd__(self, item):
        self.contents.append(item)

        if item.contains_breaks:
            self.full = True

        self._css_class = None

        return self

    def __repr__(self):

        result = '['

        if self.contents and self.contents[0].has_lhs:
            result += _str_widths_for_repr(self.contents[0].lhs)
            result += ' '

        result += ' '.join(n.word.ch for n in self.contents)

        result += ' '

        result += _str_widths_for_repr(self.contents[0].rhs)

        result += ']'

        return result

    @property
    def css_class(self):
        if self._css_class:
            return self._css_class

        def width_to_int(item):
            try:
                return item.value
            except AttributeError:
                return int(item)

        def tupleise_widths(items):
            # did I make that word up?
            return tuple([width_to_int(w) for w in items])

        key = (
                tupleise_widths(self.contents[0].lhs),
                tupleise_widths(self.contents[0].rhs),
                )

        if key in self.css_class_names:
            self._css_class = self.css_class_names[key]
            return self._css_class


        new_id = 'w%04x' % (len(self.css_class_names),)
        self.css_class_names[key] = new_id
        self._css_class = new_id
        logger.debug('created CSS class "%s" for lhs=%s, rhs=%s',
            new_id, self.contents[0].lhs, self.contents[0].rhs)

        return self._css_class

    def end_of_line_breaks(self, html):

        if not self.contents:
            return []

        result = []
        for i, width in enumerate(self.contents[-1].rhs):
            if width is not None:
                continue

            total_length = html.widths[i]
            current_length = html.current_line_lengths[i]

            br = html.result.new_tag('br')
            br['class'] = f'b{i}'
            html.current_line_lengths[i] = yex.value.Dimen()

            logger.debug('      -- created end-of-line br: %s',
                    br)

            result.append(br)

        return result

    @classmethod
    def styles_for_all_classes(cls, widths_version):
        result = ''

        for details, name in cls.css_class_names.items():

            def css_values(w):
                if w is None:
                    return '0'

                return str(yex.value.Dimen(w, 'sp'))

            lhs = details[0][widths_version]
            rhs = details[1][widths_version]

            if not lhs and not rhs:
                continue

            result += f'.{name} {{'

            if lhs:
                result += 'padding-left:'+css_values(lhs)+';'

            if rhs:
                result += 'padding-right:'+css_values(rhs)

            result += '}\n'

        return result

    def __iter__(self):
        return self.contents.__iter__()
