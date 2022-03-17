from mex.output.superclass import Output
import mex.output.svg_template
import logging

logger = logging.getLogger('mex.general')

PIXELS_PER_MM = 3.78 # yes, but why?

class Svg(Output):

    filename_extension = 'svg'

    def __init__(self,
            filename):

        if filename is None:
            self.filename = 'mex.svg' # TODO
        else:
            self.filename = filename

        self.params = {
                # All measurements in millimetres

                # A4
                'pagewidth': 210,
                'pageheight': 297,

                'gutter': 10,

                }

        self.document = _Document(driver=self)
        self.page = _Page(driver=self)

        self.document.add_child(self.page)

    def add_box(self, box):
        logger.info("Got box: %s", box)

    def close(self):
        with open(self.filename, 'w') as f:
            f.write(self.document.output())

# rather hacky specialised DOM-alike while I tune parameters and things

class _Element:

    def __init__(self,
            driver,
            ):
        self.driver = driver
        self.parent = None
        self.children = []

    def output(self):
        params = self.driver.params
        params = self.params(others=params)
        p = self.parent
        while p is not None:
            params = p.params(others = params)
            p = p.parent

        params['contents'] = ''

        for child in self.children:
            params['contents'] += child.output()

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
                'docwidth': len(self.children)*others['pagewidth'] + \
                        others['gutter']*2,
                'docheight': others['pageheight'] + others['gutter']*2,
                }
        result['viewbox'] = '0 0 %0.3f %0.3f' % (
                result['docwidth']*PIXELS_PER_MM,
                result['docheight']*PIXELS_PER_MM,
                )
        return result

class _Page(_Element):
    def __init__(self,
            driver,
            ):
        super().__init__(driver)
        self.number = 1 # for now

    def params(self, others):
        return others | {
                'number': self.number,
                'x': others['gutter'] + \
                        (others['pagewidth']+others['gutter'])*(self.number-1),
                'y': others['gutter'],
                }
