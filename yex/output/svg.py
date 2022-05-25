from yex.output.superclass import Output
import yex.output.svg_template
from yex.value.dimen import Dimen
import yex.box
import logging
import copy
import collections
import base64
import io
import string

logger = logging.getLogger('yex.general')

SCALED_PTS_PER_PIXEL = 1.333 * 65536.0 # yes, but why?

class Svg(Output):

    filename_extension = 'svg'

    def __init__(self,
            doc,
            filename):

        if filename is None:
            self.filename = 'yex.svg' # TODO
        else:
            self.filename = filename

        self.doc = doc

        self.params = {
                'gutter': Dimen(10, 'pt'),

                'x': Dimen(), 'y': Dimen(),

                'pagewidth': Dimen(),
                'pageheight': Dimen(),

                }

        self.document = _Document(driver=self)
        self.page = _Page(driver=self)

        self.document.add_another(self.page)

        self.names = collections.Counter()

    def add_box(self, yexbox,
            x=None, y=None,
            parent=None,
            tree_depth=0):

        logger.debug("%*sRendering box %s...",
            tree_depth*2, '', yexbox)

        svgclass = yexbox.__class__.__name__.lower()

        parent = parent or self.page

        x = x or Dimen()
        y = y or self.params['pageheight']

        y = y + yexbox.shifted_by

        box_x = x+self.params['gutter']*2
        box_y = (y-yexbox.height)+self.params['gutter']*2

        if parent==self.page:
            self.params['pagewidth'] = max(
                    self.params['pagewidth'],
                    yexbox.width,
                    )

        if isinstance(yexbox, yex.box.CharBox):

            css_symbol = yexbox.ch
            if css_symbol not in string.ascii_lowercase+string.digits:
                css_symbol = '%04x' % (ord(css_symbol),)

            svgbox = _Char(
                    driver = self,
                    svgclass=f'{svgclass} letter-{css_symbol}',
                    id=self.name(svgclass),
                    x = box_x,
                    y = box_y,
                    ch = yexbox.ch,
                    width=yexbox.width,
                    height=yexbox.height+yexbox.depth,
                    )
        else:
            svgbox = _Box(
                    driver = self,
                    svgclass=svgclass,
                    id=self.name(svgclass),
                    x = box_x,
                    y = box_y,
                    width=yexbox.width,
                    height=yexbox.height+yexbox.depth,
                    )

        parent.add_another(svgbox)

        for yexanother in yexbox.contents:
            self.add_box(yexanother,
                    x = x, y = y,
                    parent = svgbox,
                    tree_depth = tree_depth+1,
                    )

            if isinstance(yexbox, yex.box.VBox):
                y = y + yexanother.height
            else:
                x = x + yexanother.width

        if parent==self.page:
            self.params['pageheight'] += yexbox.height+yexbox.depth

        logger.debug("%*sdone: %s",
            tree_depth*2, '', svgbox)

        return svgbox

    def name(self, base):
        self.names[base] += 1
        return '%s%d' % (base, self.names[base])

    def glyph(self, ch):
        image = self.doc['_font'][ch].glyph.image

        with io.BytesIO() as b:
            image.save(b, format='PNG')
            result = b'data:image/png;base64,'+base64.b64encode(
                    b.getbuffer())
            result = result.decode('ASCII')

        return result, image.width, image.height

    def render(self, boxes):

        for box in boxes:
            self.add_box(box)

        # good grief, this is hacky
        the_hbox = self.page.anotherren[0]

        edges = self.params['gutter']*4

        self.params['pagewidth'] = the_hbox._params['width']+edges
        self.params['pageheight'] = the_hbox._params['height']+edges

        logger.debug("%s: writing out...",
            self)

        with open(self.filename, 'w') as f:
            f.write(self.document.output(
                **self.params,
                ))

        logger.debug('%s: done! Filename is "%s".',
                self, self.filename)

    def __repr__(self):
        return f'[svg output;d={self.doc};f={self.filename}]'

# rather hacky specialised DOM-alike while I tune parameters and things

class _Element:

    def __init__(self,
            driver,
            ):
        self.driver = driver
        self.parent = None
        self.anotherren = []

    def output(self, **kwargs):

        params = copy.deepcopy(kwargs)
        params |= self.params(params)
        contents = ''

        for another in self.anotherren:
            contents += another.output(**params)

        params['contents'] = contents

        result = self.template() % params
        return result

    def add_another(self, another):
        self.anotherren.append(another)
        another.parent = self

    @classmethod
    def template(cls):
        result = getattr(yex.output.svg_template,
                cls.__name__[1:].upper())
        return result

    def __repr__(self):
        return self.__class__.__name__

class _Document(_Element):
    def params(self, others):

        result = others | {
                'docwidth': others['pagewidth']*len(self.anotherren) + \
                        others['gutter']*2,
                'docheight': others['pageheight'] + others['gutter']*2,
                }
        return result

class _Page(_Element):
    def __init__(self,
            driver,
            ):
        super().__init__(driver)
        self.number = 1 # for now

    def params(self, others):
        x = others['gutter'] + \
                (others['pagewidth']+others['gutter'])*(self.number-1)
        y = others['gutter']

        return others | {
                'number': self.number,
                'x': x,
                'y': y,
                }

class _Box(_Element):
    def __init__(self,
            driver,
            svgclass,
            **kwargs):
        super().__init__(driver)
        self._params = copy.deepcopy(kwargs)
        self._params['class'] = svgclass

    def params(self, others):

        parent_x = others['x']
        parent_y = others['y']

        result = others | self._params

        if result['height']==0:
            # then inherit from parent
            result['height'] = others.get('height', 0)
            result['y'] = others['y']
        elif result['height']<0:
            result['height'] = abs(result['height'])
            result['y'] = result['y'] - result['height']

        if result['width']<0:
            result['width'] = result['width'] * -1
            result['x'] = result['x'] - result['width']

        return result

class _Char(_Element):
    def __init__(self,
            driver,
            svgclass,
            ch,
            **kwargs):
        super().__init__(driver)
        self._params = copy.deepcopy(kwargs)
        self._params['class'] = svgclass
        self._params['letter'] = ch

        # TODO Later, we should implement subsequent uses of the same
        # character using clones.
        self._params['href'], self._params['cwidth'], \
                self._params['cheight'] = driver.glyph(ch)

    def params(self, others):
        parent_x = others['x']
        parent_y = others['y']

        result = others | self._params

        return result
