from mex.output.superclass import Output
import mex.output.svg_template
from mex.value.dimen import Dimen
import mex.box
import logging

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
                'pagewidth': Dimen(80, 'mm'),
                'pageheight': Dimen(40, 'mm'),

                'gutter': Dimen(10, 'mm'),

                }

        self.document = _Document(driver=self)
        self.page = _Page(driver=self)

        self.document.add_child(self.page)

    def add_box(self, mexbox,
            x=None, y=None):
        logger.info("Got box: %s", mexbox)
        logger.info("Got box: %s %s %s",
                mexbox.width, mexbox.height, mexbox.depth)

        svgclass = mexbox.__class__.__name__.lower()

        # TODO work these out from params
        x = x or Dimen(10, "mm")
        y = y or Dimen(10, "mm")

        svgbox = _Box(
                driver = self,
                svgclass=svgclass,
                x=x, y=y,
                width=mexbox.width,
                height=mexbox.height+mexbox.depth,
                )
        self.page.add_child(svgbox)

        print(mexbox, mexbox.contents)
        for mexchild in mexbox.contents:
            self.add_box(mexchild)

    def close(self):
        with open(self.filename, 'w') as f:
            f.write(self.document.output(
                params=self.params,
                ))

# rather hacky specialised DOM-alike while I tune parameters and things

class _Element:

    def __init__(self,
            driver,
            ):
        self.driver = driver
        self.parent = None
        self.children = []

    def output(self, params):
        params = self.params(others=params)

        params['contents'] = ''

        for child in self.children:
            params['contents'] += child.output(params)

        result = self.template() % params
        return result

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def params(self, others):
        return others

    @classmethod
    def template(cls):
        return getattr(mex.output.svg_template,
                cls.__name__[1:].upper())

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
        self._params = kwargs
        self._params['class'] = svgclass

    def params(self, others):
        parent_x = others['x']
        parent_y = others['y']

        result = others | self._params

        result |= {
                'x': result['x'] + parent_x,
                'y': result['y'] + parent_y,
                }

        return result
