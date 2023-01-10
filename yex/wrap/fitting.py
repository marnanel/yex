import yex
from yex.box import *
from yex.wrap.dump import pretty_list_dump
import functools
import logging

logger = logging.getLogger('yex.general')

class Fitting:

    @classmethod
    def fit_to(cls, size, line):
        """
        Calculates how to fit a line of type to the given length.

        Args:
            size (Dimen): the width to fit this box to.
            line (array of Gismo): the items in the line of type.
        """

        size = size.value

        if not isinstance(line[-1], Breakpoint):
            raise ValueError(
                    f"fit_to: lines must end with Breakpoints: {line}")

        def length_in_sp(d):
            if isinstance(d, yex.value.Dimen):
                return d.value
            elif d=='inherit':
                return 0
            else:
                raise TypeError(d)

        width = size - sum([length_in_sp(x.width) for x in line
            if not isinstance(x, Leader)
            ])

        logger.debug(
                'fitting to %s (with %s available for glue): %s',
                size, width, pretty_list_dump(line))

        return cls(
                line=line,
                width=width,
                bp=line[-1],
                )

    def __init__(self, line, width, bp):
        self.line = line
        self.width = width
        self.sum_glue_final_total = 0
        self.bp = bp
        self.difference = self.glue_width - width
        self.adjusted_widths = {}

        if not isinstance(bp, (Breakpoint, type(None))):
            raise TypeError(f"{bp} was not a Breakpoint")

        if self.glue_width == width:
            self._exactly_right()

        elif self.glue_width > width:
            self._stretch_or_shrink(shrinking=True)

        else: # glue_width > width
            self.difference = -self.difference
            self._stretch_or_shrink(shrinking=False)

    def _exactly_right(self):
        logger.debug(
            '  -- glue width=%s; exactly what we want', self.glue_width)
        self.changeability = 0
        self.is_infinite = False
        for i, leader in enumerate(self.line):
            if isinstance(leader, yex.box.Leader):
                self.line[i] = leader.glue.space.value

    def _stretch_or_shrink(self, shrinking):

        if shrinking:
            change_in = lambda g: g.shrink
            direction = -1
            verb = 'shrink'
        else:
            change_in = lambda g: g.stretch
            direction = 1
            verb = 'stretch'

        logger.debug(
            '  -- glue width=%s, so it must %s by %s',
            self.glue_width, verb, self.difference)

        max_infinity = max([change_in(g).infinity for g in self.line
            if isinstance(g, yex.box.Leader)
            ], default=0)
        self.changeability = sum([change_in(g).value for g in self.line
            if isinstance(g, yex.box.Leader)
            and change_in(g).infinity==max_infinity])

        self.is_infinite = (max_infinity!=0)

        logger.debug(
                '   -- each %s unit should change by %s/%s',
                verb, self.difference, self.changeability)

        self.spaces = []

        if self.changeability==0:
            self.glue_set = 'FIXME' # FIXME
        else:
            self.glue_set = yex.util.fraction_to_str(
                    (self.difference*65536)//self.changeability,
                    16)
            if max_infinity!=0:
                self.glue_set += 'fi' + 'l'*max_infinity

        for leader in self.line:
            if not isinstance(leader, yex.box.Leader):
                continue

            if id(leader) not in self.adjusted_widths:
                g = leader.glue

                self.adjusted_widths[id(leader)] = adjusted_width(
                        space = g.space.value,
                        change = change_in(g).value,
                        change_infinity = change_in(g).infinity,
                        difference = self.difference,
                        changeability = self.changeability,
                        max_infinity = max_infinity,
                        is_shrinking = shrinking,
                        direction = direction,
                        )

            self.spaces.append(self.adjusted_widths[id(leader)])

            self.sum_glue_final_total += self.spaces[-1]

        if self.width>0 and self.spaces:
            self._adjust_for_rounding(is_shrinking=shrinking)

    def _adjust_for_rounding(self, is_shrinking):
        adjust_final_glue = self.width-self.sum_glue_final_total

        if adjust_final_glue:

            for i, leader in reversed(list(enumerate([
                thing for thing in self.line
                if isinstance(thing, yex.box.Leader)]))):

                adjusted = self.spaces[i] + adjust_final_glue

                if (
                        not is_shrinking
                        or
                        (adjusted >=
                            leader.space.value-leader.shrink.value)
                        ):

                        self.spaces[i] = adjusted
                        self.sum_glue_final_total += adjust_final_glue

                        logger.debug(
                                ('       -- adjusting final spacing by %s '
                                    'to avoid rounding error: %s'),
                                adjust_final_glue,
                                self.spaces,
                                )
                        return
        logger.debug(
                ('       -- we wanted to adjust the final spacing by %s '
                    'but there was no space to put it: %s'),
                adjust_final_glue,
                self.spaces,
                )

    @property
    def demerits(self):
        b = self.badness
        p = self.bp.penalty

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

    @property
    @functools.cache
    def badness(self):
        # The badness algorithm begins on p97 of the TeXbook

        if self.is_infinite:
            result = 0
            logger.debug(
                '   -- line is infinite, so badness == %s',
                result)

        elif (self.sum_glue_final_total > self.width):
            result = 1000000
            logger.debug(
                ' -- box is overfull (%s>%s), so badness == %s',
                self.sum_glue_final_total,
                self.width,
                result)

        elif self.glue_width==0:

            # the line contained no glue (and was not overfull). See
            # https://tex.stackexchange.com/questions/201932/

            if self.sum_glue_final_total < self.width:
                result = 10000
                logger.debug(
                    '   -- line had no glue, and was too short; '
                    'badness == %s',
                    result)

            else:
                result = 0
                logger.debug(
                    '   -- line had no glue, but everything fits; '
                    'badness == %s',
                    result)

        else:

            if self.changeability==0:
                result = 0
                logger.debug(
                    '   -- badness is %s', result)
            else:
                overall_adjustment = abs(sum([
                        self.spaces[i]-g.space.value
                        for (i,g) in enumerate(self.glue)
                        ]))
                result = round((overall_adjustment/self.changeability)**3 * 100)
                logger.debug(
                    '   -- badness is (%s/%s)**3 * 100 == %s',
                    overall_adjustment, self.changeability, result)

            BADNESS_LIMIT = 10000

            if result > BADNESS_LIMIT:
                result = BADNESS_LIMIT
                logger.debug(
                    '     -- clamped to %s',
                    result)

        return result

    @property
    @functools.cache
    def decency(self):
        if self.badness<13:
            result = DECENT
            logger.debug("   -- it's decent")
        elif self.glue_width>self.width:
            result = TIGHT
            logger.debug("   -- it's tight")
        elif self.badness<100:
            result = LOOSE
            logger.debug("   -- it's loose")
        else:
            result = VERY_LOOSE
            logger.debug("   -- it's very loose")

        return result

    @property
    @functools.cache
    def glue(self):
        return [leader for leader in self.line
            if isinstance(leader, yex.box.Leader)]

    @property
    @functools.cache
    def glue_width(self):
        return sum([leader.glue.space.value for leader in self.glue])

    def __repr__(self):
        return ('['
                f'{self.spaces}]'
                )

@functools.cache
def adjusted_width(space, change, difference, changeability,
        change_infinity, max_infinity, is_shrinking, direction):

    if space==0:
        return 0
    elif change_infinity<max_infinity:
        logger.debug(
                '     -- can\'t go further: %s',
            space)
        return space
    elif changeability==0:
        return space
    else:
        # Values in change are proportions

        delta = (change * difference) // changeability

        if is_shrinking:
            result = max(space-change, space-delta)
        else:
            result = space + delta

        return result
