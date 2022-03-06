import mex.value
import mex.gismo
import mex.parse
import logging

commands_logger = logging.getLogger('mex.commands')

def _require_dimen(d):
    """
    Casts d to a Dimen and returns it.

    People send us all sorts of weird numeric types, and
    we need to make sure they're Dimens before we start
    doing any maths with them.
    """
    if isinstance(d, mex.value.Dimen):
        return d
    elif d is None:
        return mex.value.Dimen()

    return mex.value.Dimen(d)

def _not_a_tokeniser(nat):
    r"""
    If nat is a Tokeniser, does nothing.
    Otherwise, raises MexError.

    Many classes can be initialised with a Tokeniser as
    their first argument. This doesn't work for boxes:
    they must be constructed using a control word.
    For example,

        2pt

    is a valid Dimen, but

        {hello}

    is not a valid Box; you must write something like

        \hbox{hello}

    to construct one. So we have this helper function
    which checks the first argument of box constructors,
    in case anyone tries it (which they sometimes do).
    """
    if isinstance(nat, mex.parse.Tokeniser):
        raise mex.exception.MexError(
                "internal error: boxes can't be constructed "
                "from Tokenisers"
                )

class Box(mex.gismo.C_Box):

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

    def __init__(self, height=None, width=None, depth=None,
            contents=None):

        _not_a_tokeniser(height)

        self.height = _require_dimen(height)
        self.width = _require_dimen(width)
        self.depth = _require_dimen(depth)

        if contents is None:
            self.contents = []
        else:
            self.contents = contents

    def set_from_tokens(self, index, tokens):
        index = self._check_index(index)

        tokens.eat_optional_equals()

        for e in mex.parse.Expander(
                tokens,
                single = True,
                ):
            box = e

        if isinstance(box, mex.box.Box):
            self.__setitem__(index, box)
        else:
            raise mex.exception.ParseError(
                    "not a box: {box}",
                    )

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

    def __eq__(self, other):
        return self._compare(other, depth = 0)

    def _compare(self, other, depth=0):
        debug_indent = '  '*depth
        commands_logger.debug("%sComparing %s and %s...",
                debug_indent,
                self, other)

        if not isinstance(other, self.__class__):
            commands_logger.debug("%s  -- types differ, %s %s so False",
                    debug_indent, other.__class__, self.__class__)
            return False

        if len(self)!=len(other):
            commands_logger.debug("%s  -- lengths differ, so False",
                    debug_indent)
            return False

        for ours, theirs in zip(self.contents, other.contents):
            commands_logger.debug("%s  -- comparing %s and %s",
                    debug_indent,
                    ours, theirs)
            if not ours._compare(theirs,
                    depth = depth+1,
                    ):
                commands_logger.debug("%s  -- they differ, so False",
                    debug_indent,
                    )
                return False

        commands_logger.debug("%s  -- all good, so True!",
                    debug_indent,
                    )
        return True

    def __repr__(self):
        result = '[' +\
                self.__class__.__name__.lower() +\
                self._repr() +\
                ']'
        return result

    def _repr(self):
        result = ''
        for i in self.contents:
            result += ':' + repr(i)

        return result

    def __len__(self):
        return len(self.contents)

    def showbox(self):
        r"""
        Returns a list of lines to be displayed by \showbox.

        We keep this separate from the repr() routine on purpose.
        The formatting and the information to display are
        too different to merge them.
        """
        result = [self._showbox_one_line()]

        for c in self.contents:
            result.extend(['.'+x for x in c.showbox()])

        return result

    def _showbox_one_line(self):
        return '\\'+self.__class__.__name__.lower()

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
        return fr'[\rule; {self.width}x({self.height}+{self.depth})]'

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

        _not_a_tokeniser(boxes)

        if boxes is None:
            self.contents = []
        else:
            self.contents = boxes

        self.shifted_by = mex.value.Dimen(0)

    def length_in_dominant_direction(self):

        for_boxes = sum([
            _require_dimen(self.dominant_accessor(n))
            for n in
            self.contents
            if isinstance(n, Box)
            ], start=mex.value.Dimen())

        for_glue = sum([
            _require_dimen(n.length.value)
            for n in
            self.contents
            if isinstance(n, mex.value.Glue)
            ], start=mex.value.Dimen())

        result = for_boxes + for_glue
        return result

    def length_in_non_dominant_direction(self, c_accessor):

        return max([
            _require_dimen(c_accessor(n))
            for n in
            self.contents
            if isinstance(n, Box)
            ])

    def fit_to(self, size):

        size = _require_dimen(size)

        length_boxes = sum([
            _require_dimen(self.dominant_accessor(n))
            for n in
            self.contents
            if isinstance(n, Box)
            ], start=mex.value.Dimen())

        glue = [n for n in
            self.contents
            if isinstance(n, mex.value.Glue)
            ]

        length_glue = sum([
            _require_dimen(g.space.value)
            for g in glue], start=mex.value.Dimen())

        natural_width = length_boxes + length_glue

        if natural_width == size:
            # easy enough
            for g in glue:
                g.length = g.space

        elif natural_width < size:

            difference = size - natural_width
            max_stretch_infinity = max([g.stretch.infinity for g in glue])
            stretchability = sum([g.stretch.value for g in glue
                if g.stretch.infinity==max_stretch_infinity])
            factor = float(difference)/stretchability

            for g in glue:
                if g.stretch.infinity<max_stretch_infinity:
                    g.length = g.space
                    continue

                g.length.value = g.space.value + factor * g.stretch.value

        else: # natural_width > size

            difference = natural_width - size
            max_shrink_infinity = max([g.shrink.infinity for g in glue])
            shrinkability = sum([g.shrink.value for g in glue
                if g.shrink.infinity==max_shrink_infinity])
            factor = float(difference)/shrinkability

            for g in glue:
                if g.shrink.infinity<max_shrink_infinity:
                    g.length = g.space
                    continue

                g.length.value = g.space.value - factor * g.shrink.value

                if g.length.value < g.space.value-g.shrink.value:
                    g.length.value = g.space.value-g.shrink.value

    def append(self, thing):
        self.contents.append(thing)

    def extend(self, things):
        self.contents.extend(things)

    def debug_plot(self, x, y, target):

        super().debug_plot(x, y, target)

        for c in self.contents:
            if isinstance(c, mex.value.Glue):
                pass # TODO
            else:
                c.debug_plot(x, y, target)
                dx, dy = self._offset_fn(c)
                x += dx
                y += dy

    def _showbox_one_line(self):
        def to_points(n):
            return n/65535.0

        result = r'\%s(%0.06g+%0.06g)+%0.06g' % (
                self.__class__.__name__.lower(),
                to_points(self.height),
                to_points(self.depth),
                to_points(self.width),
                )

        if self.shifted_by.value:
            result += ', shifted %0.06g' % (
                    to_points(self.shifted_by),
                    )

        return result

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
    """
    A CharBox is a Box based on a character from a mex.font.Font.
    """
    def __init__(self, font, ch):

        metric = font.metrics[ch]
        super().__init__(
                height = mex.value.Dimen(metric.height, 'pt'),
                width = mex.value.Dimen(metric.width, 'pt'),
                depth = mex.value.Dimen(metric.depth, 'pt'),
                )

        self.font = font
        self.ch = ch

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

    def showbox(self):
        return ['%s %s' % (self.font, self.ch)]
