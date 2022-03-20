from yex.output.superclass import Output
import yex.output.svg_template
from yex.value.dimen import Dimen
import yex.box
import logging
import copy
import collections
import base64
import io

logger = logging.getLogger('yex.commands')

SCALED_PTS_PER_PIXEL = 1.333 * 65536.0 # yes, but why?

class Svg(Output):

    filename_extension = 'svg'

    def __init__(self,
            state,
            filename):

        if filename is None:
            self.filename = 'yex.svg' # TODO
        else:
            self.filename = filename

        self.state = state

        self.params = {
                'gutter': Dimen(10, 'pt'),

                'x': Dimen(), 'y': Dimen(),
                }

        self.document = _Document(driver=self)
        self.page = _Page(driver=self)

        self.document.add_child(self.page)

        self.names = collections.Counter()

    def add_box(self, yexbox,
            x=None, y=None,
            parent=None):

        svgclass = yexbox.__class__.__name__.lower()

        parent = parent or self.page

        x = x or Dimen()
        y = y or Dimen()

        y = y + yexbox.shifted_by

        box_x = x+self.params['gutter']*2
        box_y = (y-yexbox.height)+self.params['gutter']*2

        if isinstance(yexbox, yex.box.CharBox):
            svgbox = _Char(
                    driver = self,
                    svgclass=svgclass,
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

        parent.add_child(svgbox)

        for yexchild in yexbox.contents:
            self.add_box(yexchild,
                    x = x, y = y,
                    parent = svgbox,
                    )
            x = x + yexchild.width

        return svgbox

    def name(self, base):
        self.names[base] += 1
        return '%s%d' % (base, self.names[base])

    def glyph(self, ch):
        image = self.state['_font'][ch].glyph.image

        with io.BytesIO() as b:
            image.save(b, format='PNG')
            result = b'data:image/png;base64,'+base64.b64encode(
                    b.getbuffer())
            result = result.decode('ASCII')

        return result, image.width, image.height

    def close(self):

        # good grief, this is hacky
        the_hbox = self.page.children[0]

        edges = self.params['gutter']*4

        self.params['pagewidth'] = the_hbox._params['width']+edges
        self.params['pageheight'] = the_hbox._params['height']+edges

        with open(self.filename, 'w') as f:
            f.write(self.document.output(
                **self.params,
                ))

# rather hacky specialised DOM-alike while I tune parameters and things

class _Element:

    def __init__(self,
            driver,
            ):
        self.driver = driver
        self.parent = None
        self.children = []

    def output(self, **kwargs):

        params = copy.deepcopy(kwargs)
        params |= self.params(params)
        contents = ''

        for child in self.children:
            contents += child.output(**params)

        params['contents'] = contents

        result = self.template() % params
        return result

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

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
                'docwidth': others['pagewidth']*len(self.children) + \
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
            result['height'] = others['height']
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
