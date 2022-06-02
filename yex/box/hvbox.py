import yex.value
from yex.box.box import *
from yex.box.gismo import *
import yex.parse
import logging
import yex

logger = logging.getLogger('yex.general')

class HVBox(Box):
    """
    A HVBox is a Box which contains some number of Gismos, in some order.

    This is an abstract class; its descendants HBox and VBox are
    the ones you want to actually use.

    Attributes:

        badness (int): a measure of how well this box can fit on a line.
            This gets set by fit_to(), which receives the length of line
            we're looking for. Before fit_to() is called, it's 0.
        decency (int): a measure of how loose the spacing is.
            This gets set by fit_to(). Before fit_to() is called, it's None.

        VERY_LOOSE: for lines with far too much space between the words
        LOOSE: for lines with too much space between the words
        DECENT: for lines with sensible amounts of space between the words
        TIGHT: for lines with too little space between the words
    """

    VERY_LOOSE = 0
    LOOSE = 1
    DECENT = 2
    TIGHT = 3

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

        self.badness = 0 # positively angelic 😇
        self.decency = self.DECENT

    def length_in_dominant_direction(self):

        lengths = [
            self.dominant_accessor(n)
            for n in
            self.contents
            ]

        result = sum(lengths, start=yex.value.Dimen())

        logger.debug(
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

        result = max(lengths, default=yex.value.Dimen())

        logger.debug(
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
        raise NotImplementedError("Going away!")
        size = require_dimen(size)

        logger.debug(
                '%s: fitting our length to %s',
                self, size)

        length_boxes = [
            self.dominant_accessor(n)
            for n in
            self.contents
            if not isinstance(n, Leader)
            ]

        sum_length_boxes = sum(length_boxes,
            start=yex.value.Dimen())

        logger.debug(
                '%s: -- contents, other than leaders, sum to %s and are: %s',
                self, sum_length_boxes, length_boxes)

        leaders = [
                n for n in self.contents
                if isinstance(n, Leader)
                ]

        length_glue = [
                leader.glue.space
                for leader in leaders
                ]

        sum_length_glue = sum(length_glue,
            start=yex.value.Dimen())

        logger.debug(
                '%s: -- leaders sum to %s and are: %s',
                self, sum_length_glue, leaders)

        natural_width = sum_length_boxes + sum_length_glue

        sum_glue_final_total = yex.value.Dimen()
        is_infinite = False
        new_leaders = []

        if natural_width == size:
            logger.debug(
                '%s: -- natural width==%s, which is equal to the new size',
                self, natural_width)
            factor = 0

        elif natural_width < size:
            difference = size - natural_width
            logger.debug(
                '%s: -- natural width==%s, so it must get longer by %s',
                self, natural_width, difference)

            max_stretch_infinity = max([g.stretch.infinity for g in leaders],
                    default=0)
            stretchability = float(sum([g.stretch for g in leaders
                if g.stretch.infinity==max_stretch_infinity]))

            if max_stretch_infinity!=0:
                is_infinite = True

            if stretchability==0:
                factor = None
            else:
                factor = float(difference)/stretchability
                if max_stretch_infinity==0:
                    logger.debug(
                            '%s:   -- each unit of stretchability '
                            'should change by %0.04g',
                        self, factor)

            for i, leader in enumerate(leaders):
                g = leader.glue
                logger.debug(
                    '%s:   -- considering %s',
                    self, g)

                if g.stretch.infinity<max_stretch_infinity:
                    new_width = g.space
                    logger.debug(
                            '%s:     -- it can\'t stretch further: %g',
                        self, new_width)
                    new_leaders.append(yex.box.Leader(
                            glue = yex.value.Glue(
                                space = g.space,
                                )))
                    continue

                if max_stretch_infinity==0:
                    # Values in g.stretch are actual lengths
                    new_width = g.space + g.stretch*factor
                else:
                    # Values in g.stretch are proportions
                    new_width = g.space + (
                            difference * (float(g.stretch)/stretchability))

                logger.debug(
                        '%s:     -- new width: %g',
                    self, new_width)

                new_leaders.append(yex.box.Leader(
                        glue = yex.value.Glue(
                            space = new_width,
                            )))

                sum_glue_final_total += new_width

        else: # natural_width > size

            difference = natural_width - size

            logger.debug(
                '%s: natural width==%s, so it must get shorter by %s',
                self, natural_width, difference)

            max_shrink_infinity = max([g.shrink.infinity for g in leaders],
                    default=0)
            shrinkability = float(sum([g.shrink for g in leaders
                if g.shrink.infinity==max_shrink_infinity],
                start=yex.value.Dimen()))

            if max_shrink_infinity!=0:
                is_infinite = True

            if shrinkability==0:
                factor = None
            else:
                factor = float(difference)/shrinkability
                if max_shrink_infinity==0:
                    logger.debug(
                            '%s:   -- each unit of shrinkability '
                            'should change by %0.04g',
                        self, factor)

            rounding_error = 0.0

            for i, leader in enumerate(leaders):
                g = leader.glue

                logger.debug(
                    '%s:   -- considering %s',
                    self, g)

                if g.shrink.infinity<max_shrink_infinity:
                    new_width = g.space
                    logger.debug(
                            '%s:     -- it can\'t shrink further: %g',
                        self, new_width)
                    new_leaders.append(yex.box.Leader(
                            glue = yex.value.Glue(
                                space = g.space,
                                )))
                    continue

                rounding_error_delta = (
                        g.space.value - g.shrink.value*factor)%1

                new_width = g.space - g.shrink * factor

                if new_width.value < g.space.value-g.shrink.value:
                    new_width.value = g.space.value-g.shrink.value
                else:
                    rounding_error += rounding_error_delta
                    logger.debug(
                            '%s:     -- rounding error += %g, to %g',
                        self, rounding_error_delta, rounding_error)

                logger.debug(
                        '%s:     -- new width: %g',
                    self, new_width)

                new_leaders.append(yex.box.Leader(
                        glue = yex.value.Glue(
                            space = new_width,
                            )))

                sum_glue_final_total += new_width

            if new_leaders and rounding_error!=0.0:
                logger.debug(
                        '%s:     -- %s',
                    self, new_leaders[-1].glue.space.value)
                logger.debug(
                        '%s:     -- adjusting %s for rounding error of %.6gsp',
                    self, new_leaders[-1], rounding_error)
                adjusted = new_leaders[-1].glue.space + yex.value.Dimen(
                        rounding_error, 'sp')
                new_leaders[-1].glue = yex.value.Glue(
                        space = adjusted,
                        )
                logger.debug(
                        '%s:     -- %s',
                    self, new_leaders[-1].glue.space.value)

        # The badness algorithm begins on p97 of the TeXbook

        sum_length_final_total = sum_glue_final_total + sum_length_boxes

        if new_leaders:
            result = []
            logger.debug(
                ' -- %s',
                self.contents)
            logger.debug(
                ' -- %s',
                new_leaders)
            for n in self.contents:
                if isinstance(n, Leader):
                    result.append(new_leaders.pop(0))
                else:
                    result.append(n)
            self.contents = result
            logger.debug(
                ' -- %s',
                self.contents)

        if is_infinite:
            badness = 0
            logger.debug(
                '%s: -- box is infinite, so badness == 0',
                self)

        elif (sum_length_final_total > size):
            badness = 1000000
            logger.debug(
                '%s: -- box is overfull (%s>%s), so badness == %s',
                self, sum_length_final_total, size, badness)

        elif factor==None:
            # the line contained no glue (and was not overfull). See
            # https://tex.stackexchange.com/questions/201932/

            if sum_length_final_total < size:
                badness = 10000
            else:
                badness = 0

        else:
            badness = int(round(factor**3 * 100))
            logger.debug(
                '%s: -- badness is (%s**3 * 100) == %d',
                self, factor, badness)

            BADNESS_LIMIT = 10000

            if badness > BADNESS_LIMIT:
                badness = BADNESS_LIMIT
                logger.debug(
                    '%s:   -- clamped to %d',
                    self, badness)

        if badness_param is not None:
            badness_param.value = badness

        if badness<13:
            decency = self.DECENT
            logger.debug("%s:   -- it's decent", self)
        elif natural_width>size:
            decency = self.TIGHT
            logger.debug("%s:   -- it's tight", self)
        elif badness<100:
            decency = self.LOOSE
            logger.debug("%s:   -- it's loose", self)
        else:
            decency = self.VERY_LOOSE
            logger.debug("%s:   -- it's very loose", self)

        logger.debug(
            '%s: -- done!',
            self)

        self.badness = badness
        self.decency = decency

        return badness, decency

    def append(self, thing):

        self.contents.append(thing)

        logger.debug(
                '%s: appended; now: %s',
                self, self.contents)

    def extend(self, things):
        for thing in things:
            self.append(thing)

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
    """
    A box whose contents are arranged horizontally.

    Text in HBoxes can be wordwrapped at points called Breakpoints.
    HBoxes insert Breakpoints as they go along.
    """

    dominant_accessor = lambda self, c: c.width

    def _offset_fn(self, c):
        return c.width

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
    def demerits(self):
        """
        The demerits of this HBox, considered as a line of type.

        The algorithm is at the foot of p97 of the TeXBook.

        Raises:
            ValueError: if this box does not end with a Breakpoint.
        """
        raise NotImplementedError("Going away!")

        try:
            final = self.contents[-1]
        except IndexError:
            raise ValueError("An empty list has no demerits")

        if not isinstance(final, Breakpoint):
            raise ValueError(
                    "Only lists ending with Breakpoints have demerits")

        b = self.badness
        p = final.penalty

        linepenalty = 10
        # TODO when we have access to the doc, look this up-- see issue #50

        result = (linepenalty + b)**2

        if p>=0:
            result += p**2
        elif p>-10000:
            result -= p**2

        logger.debug("%s: demerits==%s (b==%s, p==%s, l==%s)",
                self, result, b, p, linepenalty)

        return result

class WordBox(HBox):
    """
    A sequence of characters from a yex.font.Font.

    Not something in TeX. This exists because the TeXbook says
    about character tokens in horizontal mode (p282):

    "If two or more commands of this type occur in succession,
    TeX processes them all as a unit, converting to ligatures
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
            previous = self.contents[-1].ch
        except IndexError as e:
            pass
        except AttributeError as e:
            pass

        if previous is not None:
            pair = previous + ch

            kern_size = font_metrics.kerns.get(pair, None)

            if kern_size is not None:
                new_kern = Kern(width=-kern_size)
                logger.debug("%s: adding kern: %s",
                        self, new_kern)

                self.contents.append(new_kern)

            else:

                ligature = font_metrics.ligatures.get(pair, None)

                if ligature is not None:
                    logger.debug('%s:  -- add ligature for "%s"',
                            self, pair)

                    self.contents[-1].from_ligature = (
                        self.contents[-1].from_ligature or
                            self.contents[-1].ch) + ch

                    self.contents[-1].ch = ligature
                    return

        logger.debug("%s: adding %s after %s",
                self, ch, previous)
        self.contents.append(new_char)

    @property
    def ch(self):
        return ''.join([yex.util.only_ascii(c.ch) for c in self.contents
                if isinstance(c, CharBox)])

    def __repr__(self):
        return f'[wordbox:{self.ch}]'

    def showbox(self):
        r"""
        Returns a list of lines to be displayed by \showbox.

        WordBox doesn't appear in the output because it's not
        something that TeX displays.
        """
        return sum(
                [x.showbox() for x in self.contents],
                [])

class VBox(HVBox):

    dominant_accessor = lambda self, c: c.height+c.depth

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.contents = self.contents

    def _offset_fn(self, c):
        return yex.value.Dimen(), c.height+c.depth

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
            return yex.value.Dimen()

        return bottom.depth

class VtopBox(VBox):
    pass

class WordBox(HBox):
    """
    A sequence of characters from a yex.font.Font.

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
            previous = self.contents[-1].ch
        except IndexError as e:
            pass
        except AttributeError as e:
            pass

        if previous is not None:
            pair = previous + ch

            kern_size = font_metrics.kerns.get(pair, None)

            if kern_size is not None:
                new_kern = Kern(width=-kern_size)
                logger.debug("%s: adding kern: %s",
                        self, new_kern)

                self.contents.append(new_kern)

            else:

                ligature = font_metrics.ligatures.get(pair, None)

                if ligature is not None:
                    logger.debug('%s:  -- add ligature for "%s"',
                            self, pair)

                    self.contents[-1].from_ligature = (
                        self.contents[-1].from_ligature or
                            self.contents[-1].ch) + ch

                    self.contents[-1].ch = ligature
                    return

        logger.debug("%s: adding %s after %s",
                self, ch, previous)
        self.contents.append(new_char)

    @property
    def ch(self):
        return ''.join([yex.util.only_ascii(c.ch) for c in self.contents
                if isinstance(c, CharBox)])

    def __repr__(self):
        return f'[wordbox:{self.ch}]'

    def showbox(self):
        r"""
        Returns a list of lines to be displayed by \showbox.

        WordBox doesn't appear in the output because it's not
        something that TeX displays.
        """
        return sum(
                [x.showbox() for x in self.contents],
                [])
