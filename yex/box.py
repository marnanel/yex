import yex.value
from yex.gismo import require_dimen, not_a_tokenstream
import yex.parse
import logging

commands_logger = logging.getLogger('yex.commands')

class Box(yex.gismo.C_Box):

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
            contents=None,
            ):

        not_a_tokenstream(height)

        self.height = require_dimen(height)
        self.width = require_dimen(width)
        self.depth = require_dimen(depth)

        if contents is None:
            self.contents = []
        else:
            self.contents = contents

    def set_from_tokens(self, index, tokens):
        index = self._check_index(index)

        tokens.eat_optional_equals()

        for e in tokens.single_shot():
            box = e

        if isinstance(box, yex.box.Box):
            self.__setitem__(index, box)
        else:
            raise yex.exception.ParseError(
                    "not a box: {box}",
                    )

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
        result = r'[\%s:%04x]' % (
                self.__class__.__name__.lower(),
                id(self) % 0xffff,
                )
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

    def is_void(self):
        return self.contents==[]

class Rule(Box):
    """
    A Rule is a box which appears black on the page.
    """
    def __str__(self):
        return fr'[\rule; {self.width}x({self.height}+{self.depth})]'

class HVBox(Box):
    """
    A HVBox is a Box which contains some number of Gismos, in some order.

    This is an abstract class; its descendants HBox and VBox are
    the ones you want to actually use.
    """

    def __init__(self, contents=None,
            to=None, spread=None,
            ):
        # Not calling super().__init__() so
        # it doesn't overwrite height/width

        not_a_tokenstream(contents)
        if contents is None:
            self.contents = []
        else:
            self.contents = contents

        self.to = require_dimen(to)
        self.spread = require_dimen(spread)
        self.shifted_by = yex.value.Dimen(0)

    def length_in_dominant_direction(self):

        lengths = [
            self.dominant_accessor(n)
            for n in
            self.contents
            ]

        result = sum(lengths, start=yex.value.Dimen())

        commands_logger.debug(
                '%s: lengths in dominant direction (sum=%s): %s',
                self, result, lengths)

        return result

    def length_in_non_dominant_direction(self, c_accessor,
            shifting_polarity):

        lengths = [
            c_accessor(n) + n.shifted_by*shifting_polarity
            for n in
            self.contents
            ]

        result = max(lengths)

        commands_logger.debug(
                '%s: lengths in non-dominant direction (max=%s): %s',
                self, result, lengths)

        return result

    def fit_to(self, size):

        size = require_dimen(size)

        commands_logger.debug(
                '%s: fitting our length to %s',
                self, size)


        length_boxes = [
            self.dominant_accessor(n)
            for n in
            self.contents
            if not isinstance(n, yex.gismo.Leader)
            ]

        sum_length_boxes = sum(length_boxes,
            start=yex.value.Dimen())

        commands_logger.debug(
                '%s: -- contents, other than leaders, sum to %s and are: %s',
                self, sum_length_boxes, length_boxes)

        glue = [n for n in
            self.contents
            if isinstance(n, yex.gismo.Leader)
            ]

        length_glue = [g.space for g in glue]

        sum_length_glue = sum(length_glue,
            start=yex.value.Dimen())

        commands_logger.debug(
                '%s: -- leaders sum to %s and are: %s',
                self, sum_length_glue, glue)

        natural_width = sum_length_boxes + sum_length_glue

        if natural_width == size:
            commands_logger.debug(
                '%s: -- natural width==%s, which is equal to the new size',
                self, natural_width)

            # easy enough
            for g in glue:
                g.length = g.space

        elif natural_width < size:
            commands_logger.debug(
                '%s: -- natural width==%s, so it must get longer',
                self, natural_width)

            difference = size - natural_width
            max_stretch_infinity = max([g.stretch.infinity for g in glue])
            stretchability = sum([g.stretch for g in glue
                if g.stretch.infinity==max_stretch_infinity],
                start=yex.value.Dimen())
            factor = float(difference)/float(stretchability)
            commands_logger.debug(
                    '%s:   -- each unit of stretchability '
                    'should change by %0.04g',
                self, factor)

            for g in glue:
                commands_logger.debug(
                    '%s:   -- considering %s',
                    self, g)

                if g.stretch.infinity<max_stretch_infinity:
                    g.width = g.space
                    commands_logger.debug(
                            '%s:     -- it can\'t stretch further: %g',
                        self, g.width)
                    continue

                g.width = g.space + g.stretch * factor

                commands_logger.debug(
                        '%s:     -- new width: %g',
                    self, g.width)

        else: # natural_width > size

            commands_logger.debug(
                '%s: natural width==%s, so it must get shorter',
                self, natural_width)

            difference = natural_width - size
            max_shrink_infinity = max([g.shrink.infinity for g in glue])
            shrinkability = sum([g.shrink for g in glue
                if g.shrink.infinity==max_shrink_infinity],
                start=yex.value.Dimen())
            factor = float(difference)/float(shrinkability)
            commands_logger.debug(
                    '%s:   -- each unit of shrinkability '
                    'should change by %0.04g',
                self, factor)

            for g in glue:
                commands_logger.debug(
                    '%s:   -- considering %s',
                    self, g)

                if g.shrink.infinity<max_shrink_infinity:
                    g.width = g.space
                    commands_logger.debug(
                            '%s:     -- it can\'t shrink further: %g',
                        self, g.width)
                    continue

                g.width = g.space - g.shrink * factor

                if g.width.value < g.space.value-g.shrink.value:
                    g.width.value = g.space.value-g.shrink.value

                commands_logger.debug(
                        '%s:     -- new width: %g',
                    self, g.width)

        commands_logger.debug(
            '%s: -- done!',
            self)

    def append(self, thing):
        self.contents.append(thing)

    def extend(self, things):
        self.contents.extend(things)

    def _showbox_one_line(self):
        result = r'\%s(%0.06g+%0.06g)x%0.06g' % (
                self.__class__.__name__.lower(),
                self.height,
                self.depth,
                self.width,
                )

        if self.shifted_by.value:
            result += ', shifted %0.06g' % (
                    self.shifted_by,
                    )

        return result

    def _repr(self):
        result = ''

        if int(self.spread)!=0:
            result += f':spread={self.spread}'

        if int(self.to)!=0:
            result += f':to={self.to}'

        result += super()._repr()
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
        result = self.length_in_non_dominant_direction(
                c_accessor = lambda c: c.height,
                shifting_polarity = -1,
                )
        return result

    @property
    def depth(self):
        return self.length_in_non_dominant_direction(
                c_accessor = lambda c: c.depth,
                shifting_polarity = 1,
                )

class VBox(HVBox):

    dominant_accessor = lambda self, c: c.height+c.depth

    def _offset_fn(self, c):
        return 0, c.height+c.depth

    @property
    def width(self):
        return self.length_in_non_dominant_direction(
                c_accessor = lambda c: c.width,
                shifting_polarity = 1,
                )

    @property
    def height(self):
        return self.length_in_dominant_direction()

    @property
    def depth(self):
        # XXX not sure this is how it works
        return 0

class VtopBox(VBox):
    pass

class CharBox(Box):
    """
    A CharBox is a Box based on a character from a yex.font.Font.
    """
    def __init__(self, font, ch):

        metric = font[ch].metrics
        super().__init__(
                height = yex.value.Dimen(metric.height, 'pt'),
                width = yex.value.Dimen(metric.width, 'pt'),
                depth = yex.value.Dimen(metric.depth, 'pt'),
                )

        self.font = font
        self.ch = ch

    def __repr__(self):
        return f'[{self.ch}]'

    def showbox(self):
        return [r'\%s %s' % (self.font, self.ch)]

class WordBox(Box):
    """
    Not something in TeX. This exists because the TeXbook says
    about character tokens in horizontal mode (p282):

    "If two or more commands of this type occur in succession,
    TEX processes them all as a unit, converting to ligatures
    and/or inserting kerns as directed by the font information."
    """
    pass
