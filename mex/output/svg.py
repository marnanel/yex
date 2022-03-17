from mex.output.superclass import Output

class Svg(Output):

    filename_extension = 'svg'

    def __init__(self,
            filename):
        pass

    def add_page(self,
            page):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()
