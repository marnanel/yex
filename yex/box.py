import yex.value
from yex.gismo import require_dimen, not_a_tokenstream
import yex.parse
import logging
import yex

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
            self._contents = []
        else:
            self._contents = contents

        # in the general case, these are two names for the same thing
        self.contents = self._contents

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

        # we compare their contents, not their _contents, so that
        # we don't compare line breaks

        for ours, theirs in zip(self._contents, other.contents):
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
        for i in self._contents:
            result += ':' + repr(i)

        return result

    def __len__(self):
        # length does not include line breaks
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
        return self._contents==[]

    def __getitem__(self, n):
        try:
            return self.contents[n]
        except TypeError:
            if n==0:
                return self.contents
            else:
                raise IndexError(f"you can't get at the contents of {self}")

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
            self._contents = []
        else:
            self._contents = contents

        self.to = require_dimen(to)
        self.spread = require_dimen(spread)
        self.shifted_by = yex.value.Dimen(0)

        self.badness = 0 # positively angelic 😇

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

    def fit_to(self, size,
            badness_param = None,
            ):
        """
        Fits this box to the given length. The length of all glue will
        be adjusted accordingly.

        Args:
            size (Dimen): the width, for horizontal boxes, or height,
                for vertical boxes, to fit this box to.

            badness_param: if not None, a C_NumberParameter to update
                with the new badness score.
        """

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

        leaders = [
                n for n in self.contents
                if isinstance(n, yex.gismo.Leader)
                ]

        for leader in leaders:
            leader.glue.length = leader.glue.space

        length_glue = [
                leader.glue.length
                for leader in leaders
                ]

        sum_length_glue = sum(length_glue,
            start=yex.value.Dimen())

        commands_logger.debug(
                '%s: -- leaders sum to %s and are: %s',
                self, sum_length_glue, leaders)

        natural_width = sum_length_boxes + sum_length_glue

        sum_glue_final_total = yex.value.Dimen()

        if natural_width == size:
            commands_logger.debug(
                '%s: -- natural width==%s, which is equal to the new size',
                self, natural_width)
            factor = 0

        elif natural_width < size:
            difference = size - natural_width
            commands_logger.debug(
                '%s: -- natural width==%s, so it must get longer by %s',
                self, natural_width, difference)

            max_stretch_infinity = max([g.stretch.infinity for g in leaders])
            stretchability = float(sum([g.stretch for g in leaders
                if g.stretch.infinity==max_stretch_infinity]))

            factor = float(difference)/stretchability
            if max_stretch_infinity==0:
                commands_logger.debug(
                        '%s:   -- each unit of stretchability '
                        'should change by %0.04g',
                    self, factor)

            for leader in leaders:
                g = leader.glue
                commands_logger.debug(
                    '%s:   -- considering %s',
                    self, g)

                if g.stretch.infinity<max_stretch_infinity:
                    g.length = g.space
                    commands_logger.debug(
                            '%s:     -- it can\'t stretch further: %g',
                        self, g.length)
                    continue

                if max_stretch_infinity==0:
                    # Values in g.stretch are actual lengths
                    g.length = g.space + g.stretch*factor
                else:
                    # Values in g.stretch are proportions
                    g.length = g.space + (
                            difference * (float(g.stretch)/stretchability))

                commands_logger.debug(
                        '%s:     -- new width: %g',
                    self, g.length)

                leader.glue = g

                sum_glue_final_total += g

        else: # natural_width > size

            difference = natural_width - size

            commands_logger.debug(
                '%s: natural width==%s, so it must get shorter by %s',
                self, natural_width, difference)

            max_shrink_infinity = max([g.shrink.infinity for g in leaders])
            shrinkability = float(sum([g.shrink for g in leaders
                if g.shrink.infinity==max_shrink_infinity],
                start=yex.value.Dimen()))

            factor = float(difference)/shrinkability
            if max_shrink_infinity==0:
                commands_logger.debug(
                        '%s:   -- each unit of shrinkability '
                        'should change by %0.04g',
                    self, factor)

            final = None
            rounding_error = 0.0

            for leader in leaders:
                g = leader.glue

                commands_logger.debug(
                    '%s:   -- considering %s',
                    self, g)

                if g.shrink.infinity<max_shrink_infinity:
                    g.length = g.space
                    commands_logger.debug(
                            '%s:     -- it can\'t shrink further: %g',
                        self, g.length)
                    continue

                rounding_error_delta = (
                        g.space.value - g.shrink.value*factor)%1

                g.length = g.space - g.shrink * factor

                if g.length.value < g.space.value-g.shrink.value:
                    g.length.value = g.space.value-g.shrink.value
                else:
                    rounding_error += rounding_error_delta
                    commands_logger.debug(
                            '%s:     -- rounding error += %g, to %g',
                        self, rounding_error_delta, rounding_error)

                commands_logger.debug(
                        '%s:     -- new width: %g',
                    self, g.length)

                leader.glue = g
                sum_glue_final_total += g
                final = g

            if final is not None and rounding_error!=0.0:
                commands_logger.debug(
                        '%s:     -- adjusting %s for rounding error of %.6gsp',
                    self, final, rounding_error)
                final.length -= yex.value.Dimen(rounding_error, 'sp')

        # The badness algorithm begins on p97 of the TeXbook

        sum_length_final_total = sum_glue_final_total + sum_length_boxes

        if (sum_length_final_total > size):
            self.badness = 1000000
            commands_logger.debug(
                '%s: -- box is overfull (%s>%s), so badness == %s',
                self, sum_length_final_total, size, self.badness)

        else:

            self.badness = int(round(factor**3 * 100))
            commands_logger.debug(
                '%s: -- badness is (%s**3 * 100) == %d',
                self, factor, self.badness)

            BADNESS_LIMIT = 10000

            if self.badness > BADNESS_LIMIT:
                self.badness = BADNESS_LIMIT
                commands_logger.debug(
                    '%s:   -- clamped to %d',
                    self, self.badness)

        if badness_param is not None:
            badness_param.value = self.badness

        commands_logger.debug(
            '%s: -- done!',
            self)

    def append(self, thing):
        self._contents.append(thing)

    def extend(self, things):
        self._contents.extend(things)

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

class Breakpoint:
    """
    A point at which the words in an HBox could wrap to the next line.

    Chapter 14 of the TeXbook explains the algorithm.

    Attributes:
        penalty (int): the cost of breaking at this breakpoint.
    """

    def __init__(self, penalty=0):
        self.penalty = penalty

    def __repr__(self):
        return f'[{self.penalty}]'

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

    @property
    def contents(self):
        return self.contents_without_breaks

    @property
    def contents_with_breaks(self):
        return self._contents

    @property
    def contents_without_breaks(self):
        return [item for item in self._contents
                if isinstance(item, yex.gismo.Gismo)]

class VBox(HVBox):

    dominant_accessor = lambda self, c: c.height+c.depth

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.contents = self._contents

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
        return self.length_in_dominant_direction() - self.depth

    @property
    def depth(self):
        try:
            bottom = self.contents[-1]
        except IndexError:
            return 0

        return bottom.depth

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
        return [r'%s %s' % (self.font, self.ch)]

class WordBox(HBox):
    """
    A sequence of letter characters from a yex.font.Font.

    Not something in TeX. This exists because the TeXbook says
    about character tokens in horizontal mode (p282):

    "If two or more commands of this type occur in succession,
    TEX processes them all as a unit, converting to ligatures
    and/or inserting kerns as directed by the font information."
    """

    def __init__(self, font):
        super().__init__()
        self.font = font

    def append(self, ch):
        if not isinstance(ch, str):
            raise TypeError(
                    f'WordBoxes can only hold characters '
                    f'(and not {ch}, which is {type(ch)})')
        elif len(ch)!=1:
            raise TypeError(
                    f'You can only add one character at a time to '
                    f'a WordBox (and not "{ch}")')

        new_char = CharBox(
                ch = ch,
                font = self.font,
                )

        font_metrics = self.font.metrics

        previous = None
        try:
            previous = self._contents[-1].ch
        except IndexError as e:
            pass
        except AttributeError as e:
            pass

        if previous is not None:
            pair = previous + ch

            kern_size = font_metrics.kerns.get(pair, None)

            if kern_size is not None:
                new_kern = yex.gismo.Kern(width=-kern_size)
                commands_logger.debug("%s: adding kern: %s",
                        self, new_kern)

                self._contents.append(new_kern)

            else:

                ligature = font_metrics.ligatures.get(pair, None)

                if ligature is not None:
                    commands_logger.debug('%s:  -- add ligature for "%s"',
                            self, pair)

                    self._contents[-1].ch = ligature
                    return

        commands_logger.debug("%s: adding %s after %s",
                self, ch, previous)
        self._contents.append(new_char)

    @property
    def ch(self):
        return ''.join([yex.util.only_ascii(c.ch) for c in self._contents
                if isinstance(c, CharBox)])

    def __repr__(self):
        return f'[wordbox:{self.ch}]'

    def showbox(self):
        r"""
        Returns a list of lines to be displayed by \showbox.

        WordBox doesn't appear in the output because it's not
        something that TeX displays.

        Oddly enough, TeX only displays the first item in a WordBox
        but not the WordBox itself. Other TeX-like systems display
        the whole lot.  Let's do it TeX's way for now.
        """
        if self.contents:
            return self.contents[0].showbox()
        else:
            return []
