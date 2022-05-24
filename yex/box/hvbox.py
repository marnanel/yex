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
        self.badness, self.decency = self._inner_fit_to(
                size = size,
                contents = self.contents,
                badness_param = badness_param,
                )

    def _inner_fit_to(self, size, contents, badness_param):

        size = require_dimen(size)

        logger.debug(
                '%s: fitting our length to %s',
                self, size)

        length_boxes = [
            self.dominant_accessor(n)
            for n in
            contents
            if not isinstance(n, Leader)
            ]

        sum_length_boxes = sum(length_boxes,
            start=yex.value.Dimen())

        logger.debug(
                '%s: -- contents, other than leaders, sum to %s and are: %s',
                self, sum_length_boxes, length_boxes)

        leaders = [
                n for n in contents
                if isinstance(n, Leader)
                ]

        for leader in leaders:
            leader.glue.length = leader.glue.space

        length_glue = [
                leader.glue.length
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

            for leader in leaders:
                g = leader.glue
                logger.debug(
                    '%s:   -- considering %s',
                    self, g)

                if g.stretch.infinity<max_stretch_infinity:
                    g.length = g.space
                    logger.debug(
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

                logger.debug(
                        '%s:     -- new width: %g',
                    self, g.length)

                leader.glue = g

                sum_glue_final_total += g

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

            final = None
            rounding_error = 0.0

            for leader in leaders:
                g = leader.glue

                logger.debug(
                    '%s:   -- considering %s',
                    self, g)

                if g.shrink.infinity<max_shrink_infinity:
                    g.length = g.space
                    logger.debug(
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
                    logger.debug(
                            '%s:     -- rounding error += %g, to %g',
                        self, rounding_error_delta, rounding_error)

                logger.debug(
                        '%s:     -- new width: %g',
                    self, g.length)

                leader.glue = g
                sum_glue_final_total += g
                final = g

            if final is not None and rounding_error!=0.0:
                logger.debug(
                        '%s:     -- adjusting %s for rounding error of %.6gsp',
                    self, final, rounding_error)
                final.length -= yex.value.Dimen(rounding_error, 'sp')

        # The badness algorithm begins on p97 of the TeXbook

        sum_length_final_total = sum_glue_final_total + sum_length_boxes

        if is_infinite:
            badness = 0

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

        return badness, decency

    def append(self, thing):
        self.contents.append(thing)

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
    HBoxes insert Breakpoints as they go along, but their "contents"
    property always returns a copy with the Breakpoints removed.
    This saves astonishing any code which expects to find in a box
    exactly what it just put in there.

    If you want to see the Breakpoints, look in the "with_breakpoints"
    property. It returns a proxy of this object where the Breakpoints
    are visible.
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

    def append(self, thing,
            hyphenpenalty = 50,
            exhyphenpenalty = 50):

        def is_glue(thing):
            return isinstance(thing, Leader) and \
                    isinstance(thing.glue, yex.value.Glue)

        try:
            previous = self.contents[-1]
        except IndexError:
            previous = None
            super().append(Breakpoint())
            logger.debug(
                    '%s: added initial breakpoint: %s',
                    self, self.contents)

        if is_glue(thing):
            if previous is not None and not previous.discardable:
                # FIXME and it's not part of a maths formula
                super().append(Breakpoint())
                logger.debug(
                        '%s: added breakpoint before glue: %s',
                        self, self.contents)
            elif isinstance(previous, Kern):
                self.contents.pop()
                super().append(Breakpoint())
                super().append(previous)

                logger.debug(
                        '%s: added breakpoint before previous kern: %s',
                        self, self.contents)
            elif isinstance(previous,
                    MathSwitch) and previous.which==False:
                self.contents.pop()
                super().append(Breakpoint())
                super().append(previous)

                logger.debug(
                        '%s: added breakpoint before previous math-off: %s',
                        self, self.contents)

        elif isinstance(thing, Penalty):
            super().append(Breakpoint(thing.demerits))
            logger.debug(
                    '%s: added penalty breakpoint: %s',
                    self, self.contents)

        elif isinstance(thing, DiscretionaryBreak):

            try:
                if previous.ch!='':
                    demerits = exhyphenpenalty
                else:
                    demerits = hyphenpenalty
            except AtttributeError:
                demerits = exhyphenpenalty

            super().append(Breakpoint(demerits))
            logger.debug(
                    '%s: added breakpoint before discretionary break: %s',
                    self, self.contents)

        super().append(thing)

    def wrap(self, doc):

        hsize = doc[r'\hsize'].value
        pretolerance = doc[r'\pretolerance'].value

        logger.debug("%s: wrapping", self)

        # Munge this box slightly (see TeXbook p99).

        if isinstance(self.contents[-1], Leader):
            logger.debug("%s: discarding glue at the end", self)
            self.contents.pop()

        self.append(Penalty(10000))
        self.append(
                Leader(glue=doc[r'\parfillskip'].value)
                )
        self.append(Penalty(-10000))
        self.append(Breakpoint(0))

        line = self.with_breakpoints
        logger.debug("%s: so, wrapping: %s", self, line.contents)
        # Okay, let's go break some lines.

        class Badnesses:
            def __init__(self):
                self.cache = {}

            def lookup(self, left_bp, right_bp):
                print(left_bp, right_bp, len(line.contents))
                try:
                    return self.cache[(left_bp, right_bp)]
                except KeyError:
                    pass

                subsequence = line[left_bp:right_bp]

                logger.debug("Looking up badness for %s", subsequence)
                logger.debug("  -- which is %s", subsequence.contents)
                subsequence.fit_to(hsize)

                result = (
                        subsequence.badness,
                        subsequence.decency,
                        )

                logger.debug("  -- badness and decency are %s",
                        result)

                self.cache[(left_bp, right_bp)] = result

                return result

            def arcs_from(self, from_i):
                sources = set([f[0] for f in self.cache.keys()])

                return dict([
                    (f[1], v) for f,v in self.cache.items()
                    if f[0]==from_i and f[1] in sources])

            def _find_paths_inner(self, start, finish):

                print(start, finish, len(line.contents))

                arcs = self.arcs_from(start)
                result = []

                for target, v in arcs.items():
                    print("%*s%s->%s %s" % (
                            start, '', start, target, v))

                    logger.debug("%*s%s->%s %s",
                            start, '', start, target, v)

                    print(target, finish)
                    if target==finish:
                        result.append([(target, v)])
                    else:
                        next_bit = self._find_paths_inner(
                                start = target,
                                finish = finish,
                                )
                        result += [
                            [(target, v)]+path
                            for path in next_bit]

                return result

            def find_paths(self):
                result = self._find_paths_inner(
                        start=0,
                        finish=len(line.contents))

                print(result)

        badnesses = Badnesses()

        found = set([0])

        for from_i, from_bp in enumerate(line.contents[:-1]):
            if not isinstance(from_bp, Breakpoint):
                continue

            if from_i not in found:
                continue

            from_bp.number = len(found)-1
            logger.debug("%s: badness check starting from %s (%s)",
                    self, from_i, from_bp)

            for to_i, to_bp in enumerate(
                    line.contents[from_i+1:-1],
                    start=from_i+1,
                    ):
                if not isinstance(to_bp, Breakpoint):
                    continue

                badness, decency = badnesses.lookup(from_i, to_i)

                logger.debug("%s: %s->%s has badness %s and decency %s",
                        self, from_i, to_i, badness, decency)

                if badness >= 100000: # overfull; we mustn't go here!
                    logger.debug("%s: badness was high enough we'll break",
                            self)
                    break
                elif badness >= pretolerance:
                    logger.debug("%s: badness was high enough we'll ignore",
                            self)
                else:
                    found.add(to_i)

        for bp in sorted(found):
            print()
            print(bp)
            print(badnesses.arcs_from(bp))

        return
        badnesses.find_paths()

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