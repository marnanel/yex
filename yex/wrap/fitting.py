import yex
from yex.box import *
from yex.wrap.dump import pretty_list_dump
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

        glue = [n for n in line if isinstance(n, Leader)]

        glue_width = sum([leader.glue.space.value for leader in glue])

        sum_glue_final_total = 0
        is_infinite = False
        difference = width - glue_width
        adjust_final_glue = 0
        glue_set = None
        result = []

        if glue_width == width:
            logger.debug(
                '  -- glue width=%s; exactly what we want', width)
            changeability = 0

        elif glue_width < width:
            logger.debug(
                '  -- glue width=%s, so it must get longer by %s',
                glue_width, difference)

            max_stretch_infinity = max([g.stretch.infinity for g in glue],
                    default=0)
            changeability = sum([g.stretch.value for g in glue
                if g.stretch.infinity==max_stretch_infinity])

            if max_stretch_infinity!=0:
                is_infinite = True

            logger.debug(
                    '   -- each unit of stretchability '
                    'should change by %s/%s',
                    difference, changeability)

            added_width = 0

            if changeability!=0:
                glue_set = '%0.06g' % (difference/changeability,)
                if max_stretch_infinity!=0:
                    glue_set += 'fi' + 'l'*max_stretch_infinity

            for i, leader in enumerate(glue):
                g = leader.glue

                if g.stretch.infinity<max_stretch_infinity:
                    logger.debug(
                            '     -- %s: can\'t stretch further: %s',
                        g, g.space)
                    result.append(g.space.value)
                    continue

                if changeability==0:
                    new_width = g.space.value
                else:
                    # Values in g.stretch are proportions
                    delta = g.stretch.value * difference // changeability
                    new_width = g.space.value + delta
                    added_width += delta

                logger.debug(
                        '     -- %s: from %s to %s',
                    g, g.space.value, new_width)
                result.append(new_width)

                sum_glue_final_total += new_width

        else: # glue_width > width

            difference = glue_width - width

            logger.debug(
                '  -- glue width=%s, so it must get shorter by %s',
                glue_width, difference)

            max_shrink_infinity = max([g.shrink.infinity for g in glue],
                    default=0)
            changeability = sum([g.shrink.value for g in glue
                if g.shrink.infinity==max_shrink_infinity])

            if max_shrink_infinity!=0:
                is_infinite = True

            logger.debug(
                    '   -- each unit of shrinkability '
                    'should change by %s/%s',
                    difference, changeability)

            removed_width = 0

            for i, leader in enumerate(glue):
                g = leader.glue

                if g.shrink.infinity<max_shrink_infinity:
                    logger.debug(
                            '     -- %s: can\'t shrink further: %s',
                        g, g.space.value)
                    result.append(g.space.value)
                    continue

                if changeability==0:
                    new_width = g.space.value
                else:
                    new_width = g.space.value - (
                            g.shrink.value * difference // changeability )

                if new_width < g.space.value-g.shrink.value:
                    new_width = g.space.value-g.shrink.value

                logger.debug(
                        '     -- %s: new width: %s',
                    g, new_width)

                result.append(new_width)

                sum_glue_final_total += new_width
                removed_width = new_width - g.space.value

        if result and width>0:

            adjust_final_glue = width-sum(result)
            if adjust_final_glue!=0:

                for i, g in reversed(list(enumerate(glue))):
                    adjusted_width = result[i]+adjust_final_glue

                    if adjusted_width> (g.space-g.shrink):
                        result[i] = adjusted_width
                        logger.debug(
                                ('       -- adjusting glue #%s by %s '
                                    'to avoid rounding error: %s'),
                                i,
                                adjust_final_glue,
                                adjusted_width,
                                )
                        break

        logger.debug("Results: %s", result)

        # The badness algorithm begins on p97 of the TeXbook

        if is_infinite:
            badness = 0
            logger.debug(
                '   -- line is infinite, so badness == %s',
                badness)

        elif (sum_glue_final_total > width):
            badness = 1000000
            logger.debug(
                ' -- box is overfull (%s>%s), so badness == %s',
                sum_glue_final_total, width, badness)

        elif glue_width==0:

            # the line contained no glue (and was not overfull). See
            # https://tex.stackexchange.com/questions/201932/

            if sum_glue_final_total < width:
                badness = 10000
                logger.debug(
                    '   -- line had no glue, and was too short; badness == %s',
                    badness)

            else:
                badness = 0
                logger.debug(
                    '   -- line had no glue, but everything fits; badness == %s',
                    badness)

        else:

            if changeability==0:
                badness = 0
                logger.debug(
                    '   -- badness is %s', badness)
            else:
                overall_adjustment = abs(sum([
                        result[i]-g.space.value for (i,g) in enumerate(glue)
                        ]))
                badness = round((overall_adjustment/changeability)**3 * 100)
                logger.debug(
                    '   -- badness is (%s/%s)**3 * 100 == %s',
                    overall_adjustment, changeability, badness)

            BADNESS_LIMIT = 10000

            if badness > BADNESS_LIMIT:
                badness = BADNESS_LIMIT
                logger.debug(
                    '     -- clamped to %s',
                    badness)

        if badness<13:
            decency = DECENT
            logger.debug("   -- it's decent")
        elif glue_width>width:
            decency = TIGHT
            logger.debug("   -- it's tight")
        elif badness<100:
            decency = LOOSE
            logger.debug("   -- it's loose")
        else:
            decency = VERY_LOOSE
            logger.debug("   -- it's very loose")

        logger.debug(
                '  -- done!: %s',
                result)

        return cls(
                badness=badness,
                decency=decency,
                spaces=result,
                width=width,
                glue_set = glue_set,
                bp=line[-1],
                )

    def __init__(self, badness, decency, spaces, width, glue_set, bp):
        self.badness = badness
        self.decency = decency
        self.spaces = spaces
        self.glue_set = glue_set
        self.width = width

        if isinstance(bp, Breakpoint):
            self.bp = bp
        else:
            raise TypeError(f"{bp} was not a Breakpoint")

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

    def __repr__(self):
        return ('['
                f'badness={self.badness};'
                f'decency={self.decency};'
                f'glue_set={self.glue_set};'
                f'{self.spaces}]'
                )
