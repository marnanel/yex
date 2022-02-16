class Box:

    """
    A Box is a rectangle on the page. It's not necessarily visible.

    All Boxes have a width, a height, and a depth.
    Their x-dimension is their width.
    Their y-dimension is their height plus their depth.
    Any of these may be negative.

    They are measured from a point on the page called their
    "reference point", which is not stored in the Box instance
    itself. From this point, height is measured upwards,
    depth downwards, and width to the right.
    """

    def __init__(self, height, width, depth):
        self.height = height
        self.width = width
        self.depth = depth

    def debug_plot(self, x, y, target,
            ch=''):
        """
        Sends our details to the debug plotter "target".
        """

        target.draw(
                x=x, y=y,
                height=self.height,
                width=self.width,
                depth=self.depth,
                ch=ch,
                kind=self.__class__.__name__.lower())

    def __str__(self):
        return f'[{self.width}x({self.height}+{self.depth})]'

class Glue:

    def __init__(self,
        space, stretch, shrink,
        stretch_infinity = 0,
        shrink_infinity = 0,
        ):

        self.stretch = stretch
        self.stretch_infinity = stretch_infinity
        self.shrink = shrink
        self.shrink_infinity = shrink_infinity

        self.space = space
        self.length = self.space

    def __str__(self):
        result = f'[Glue: sp{self.space}'

        if self.length!=self.space:
            result += f' len{self.length}'

        result += f' st{self.stretch}'
        if self.stretch_infinity!=0:
            result += f'-inf{self.stretch_infinity}'

        result += f' sh{self.shrink}'
        if self.shrink_infinity!=0:
            result += f'-inf{self.shrink_infinity}'

        return result+']'

class Rule(Box):
    """
    A Rule is a box which appears black on the page.
    """
    def debug_plot(self, target):
        """
        Sends our details to the debug plotter "target".
        """
        pass

    def __str__(self):
        return f'[rule; {self.width}x({self.height}+{self.depth})]'

class HVBox(Box):
    """
    A HVBox is a Box which contains one or more other Boxes, or Glue,
    or both, in some order.

    This is an abstract class; its descendants HBox and VBox are
    the ones you want to actually use.
    """

    def __init__(self, boxes=None):
        # Not calling super().__init__() so
        # it doesn't overwrite height/width

        if boxes is None:
            self.contents = []
        else:
            self.contents = boxes

    def length_in_dominant_direction(self):

        for_boxes = sum([
            self.dominant_accessor(n)
            for n in
            self.contents
            if isinstance(n, Box)
            ])

        for_glue = sum([
            n.length
            for n in
            self.contents
            if isinstance(n, Glue)
            ])

        return for_boxes + for_glue

    def length_in_non_dominant_direction(self, c_accessor):

        return max([
            c_accessor(n)
            for n in
            self.contents
            if isinstance(n, Box)
            ])

    def fit_to(self, size):
        length_boxes = sum([
            self.dominant_accessor(n)
            for n in
            self.contents
            if isinstance(n, Box)
            ])

        glue = [n for n in
            self.contents
            if isinstance(n, Glue)
            ]

        length_glue = sum([g.space for g in glue])

        natural_width = length_boxes + length_glue


        if natural_width == size:
            # easy enough
            for g in glue:
                g.length = g.space

        elif natural_width < size:

            difference = size - natural_width
            max_stretch_infinity = max([g.stretch_infinity for g in glue])
            stretchability = sum([g.stretch for g in glue
                if g.stretch_infinity==max_stretch_infinity])
            factor = difference/stretchability

            for g in glue:
                if g.stretch_infinity<max_stretch_infinity:
                    g.length = g.space
                    continue

                g.length = g.space + factor * g.stretch

        else: # natural_width > size

            difference = natural_width - size
            max_shrink_infinity = max([g.shrink_infinity for g in glue])
            shrinkability = sum([g.shrink for g in glue
                if g.shrink_infinity==max_shrink_infinity])
            factor = difference/shrinkability

            for g in glue:
                if g.shrink_infinity<max_shrink_infinity:
                    g.length = g.space
                    continue

                g.length = g.space - factor * g.shrink

                if g.length < g.space-g.shrink:
                    g.length = g.space-g.shrink

    def __str__(self):
        return f'[{self.__class__.__name__}]'

    def append(self, thing):
        self.contents.append(thing)

    def extend(self, things):
        self.contents.extend(things)

    def debug_plot(self, x, y, target):

        super().debug_plot(x, y, target)

        for c in self.contents:
            if isinstance(c, Glue):
                pass # TODO
            else:
                c.debug_plot(x, y, target)
                dx, dy = self._offset_fn(c)
                x += dx
                y += dy

class HBox(HVBox):

    dominant_accessor = lambda self, c: c.width

    def _offset_fn(self, c):
        return c.width, 0

    @property
    def width(self):
        return self.length_in_dominant_direction()

    @property
    def height(self):
        return self.length_in_non_dominant_direction(
                lambda c: c.height,
                )

    @property
    def depth(self):
        return self.length_in_non_dominant_direction(
                lambda c: c.depth,
                )

    def _debug_plot_helper(self, x, y, target):
        super().debug_plot(x, y, target,
                lambda c: (c.width, 0),
                )

class VBox(HVBox):

    dominant_accessor = lambda self, c: c.height+c.depth

    def _offset_fn(self, c):
        return 0, c.height+c.depth

    @property
    def width(self):
        return self.length_in_non_dominant_direction(
                lambda c: c.width,
                )

    @property
    def height(self):
        return self.length_in_dominant_direction()

    @property
    def depth(self):
        # XXX not sure this is how it works
        return 0

    def debug_plot(self, x, y, target):
        self._debug_plot_helper(x, y, target,
                lambda c: (0, c.height+c.depth),
                )

class CharBox(Box):
    def __init__(self, char):
        """
        |char| is a mex.font.CharacterMetric.
        """
        self.ch = chr(char.codepoint)
        self.width = char.width
        self.height = char.height
        self.depth = char.depth

    def __repr__(self):
        return f'[{self.ch}]'

    def debug_plot(self, x, y, target):
        target.draw(
                x=x, y=y,
                height=self.height,
                width=self.width,
                depth=self.depth,
                ch=self.ch,
                kind='char')
