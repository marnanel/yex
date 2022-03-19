from mex.output.superclass import Output
import mex.output.svg_template
from mex.value.dimen import Dimen
import mex.box
import logging
import copy
import collections

logger = logging.getLogger('mex.commands')

SCALED_PTS_PER_PIXEL = 1.333 * 65536.0 # yes, but why?

class Svg(Output):

    filename_extension = 'svg'

    def __init__(self,
            filename):

        if filename is None:
            self.filename = 'mex.svg' # TODO
        else:
            self.filename = filename

        self.params = {
                # A4
                #'pagewidth': Dimen(210, 'mm'),
                #'pageheight': Dimen(297, 'mm'),

                # for testing
                'pagewidth': Dimen(80, 'pt'),
                'pageheight': Dimen(40, 'pt'),

                'gutter': Dimen(10, 'pt'),

                'x': Dimen(), 'y': Dimen(),
                }

        self.document = _Document(driver=self)
        self.page = _Page(driver=self)

        self.document.add_child(self.page)

        self.names = collections.Counter()

    def add_box(self, mexbox,
            x=None, y=None,
            parent=None):

        svgclass = mexbox.__class__.__name__.lower()

        x = x or self.params['gutter']
        y = y or self.params['gutter']

        parent = parent or self.page

        svgbox = _Box(
                driver = self,
                svgclass=svgclass,
                id=self.name(svgclass),
                x=x, y=y-mexbox.height,
                width=mexbox.width,
                height=mexbox.height+mexbox.depth,
                )
        parent.add_child(svgbox)

        for mexchild in mexbox.contents:
            self.add_box(mexchild,
                    x = x, y = y,
                    parent = svgbox,
                    )
            x = x + mexchild.width

        return svgbox

    def name(self, base):
        self.names[base] += 1
        return '%s%d' % (base, self.names[base])

    def close(self):

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
        result = getattr(mex.output.svg_template,
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
        print(kwargs)
        self._params = copy.deepcopy(kwargs)
        self._params['class'] = svgclass

    def params(self, others):
        parent_x = others['x']
        parent_y = others['y']

        result = others | self._params
        result['x'] = 0
        result['y'] = 0

        return result
