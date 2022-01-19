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

    def debug_plot(self, x, y, target):
        """
        Sends our details to the debug plotter "target".
        """
        pass

    def __str__(self):
        return f'[{self.width}x({self.height}+{self.depth})]'

class Glue:
    pass

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

    def __init__(self, *args, **kwargs):
        # Not calling super().__init__() so
        # it doesn't overwrite height/width

        self.contents = []

    def _length_in_dominant_direction(self,
            child_accessor):

        return sum([
            child_accessor(n)
            for n in
            self.contents
            ])

    def _length_in_non_dominant_direction(self,
            child_accessor):

        return max([
            child_accessor(n)
            for n in
            self.contents
            ])

    def __str__(self):
        return f'[{self.__class__.__name__}]'

    def append(self, thing):
        self.contents.append(thing)

    def debug_plot(self, x, y, target, offset_fn):
        for c in self.contents:
            c.debug_plot(x, y, target)
            dx, dy = offset_fn(c)
            x += dx
            y += dy

class HBox(HVBox):

    @property
    def width(self):
        return self._length_in_dominant_direction(
                lambda c: c.width,
                )

    @property
    def height(self):
        return self._length_in_non_dominant_direction(
                lambda c: c.height,
                )

    @property
    def depth(self):
        return self._length_in_non_dominant_direction(
                lambda c: c.depth,
                )

    def debug_plot(self, x, y, target):
        super().debug_plot(x, y, target,
                lambda c: (c.width, 0),
                )

class VBox(HVBox):
    @property
    def width(self):
        return self._length_in_non_dominant_direction(
                lambda c: c.width,
                )

    @property
    def height(self):
        return self._length_in_dominant_direction(
                lambda c: c.height+c.depth,
                )

    @property
    def depth(self):
        return 0 # XXX is this really how it works?

    def debug_plot(self, x, y, target):
        super().debug_plot(x, y, target,
                lambda c: (0, c.height+c.depth),
                )

class CharBox(Box):
    def __init__(self, char):
        """
        |char| is a mex.font.CharacterMetric.
        """
        self.char = char

    @property
    def width(self):
        return self.char.width

    @property
    def height(self):
        return self.char.height

    @property
    def depth(self):
        return self.char.depth


