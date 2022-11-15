"""
Wraps paragraphs into lines.

See chapter 14 of the TeXbook for details.
"""

import yex
import yex.value
import yex.parse
from yex.box import *
import logging

logger = logging.getLogger('yex.general')

VERY_LOOSE = 0
LOOSE = 1
DECENT = 2
TIGHT = 3

def wrap(items, doc):
    r"""
    Wraps a list of Gismos into lines.

    The width of each items is based on doc['\hsize'], though there are
    several other considerations.

    See chapter 14 of the TeXbook for details.

    Arguments:
        items (list of `Gismo`): the things to wrap
        doc: the document they're going into

    Returns:
        a `VBox` of `HBox`s containing the items, wrapped into lines.
        (Some of the discardable items may have been removed.)
    """

    if not items:
        return VBox()

    widths = Widths(doc)
    pretolerance = doc[r'\pretolerance']

    trace = doc.get(r'\tracingparagraphs', param_control=True)

    items = prep_list(doc, items)

    logger.debug("wrap: starting with %s", pretty_list_dump(items))
    # Okay, let's go break some lines.

    subsequences = Subsequence_Cache(items=items)

    items[0].number = 0
    items[0].total_demerits = 0

    breakpoint_count = 1
    starting_place = 0

    for to_i, to_bp in enumerate(items[:-1]):
        if not isinstance(to_bp, Breakpoint):
            continue

        logger.debug("wrap: .... %18s to %4s (%10s)",
                '', to_i, to_bp)

        possibles = []

        for from_i, from_bp in list(
                enumerate(items)
                )[starting_place:to_i]:

            if not isinstance(from_bp, Breakpoint):
                continue

            if from_bp.total_demerits is None:
                continue

            logger.debug("wrap: from %4s (%10s), to %4s (%10s)",
                    from_i, from_bp, to_i, to_bp)

            found = subsequences.lookup(from_i, to_i,
                    width = widths[from_bp.line_number])

            logger.debug("%s->%s has badness %s and decency %s",
                    from_i, to_i, found.badness, found.decency)

            if found.badness > pretolerance:
                logger.debug("badness was high enough we'll ignore")
            else:
                possibles.append(
                        (from_bp, found)
                        )

        if not possibles:
            continue

        best = min(possibles, key=lambda p: p[0].total_demerits+p[1].demerits)

        to_bp.total_demerits = best[0].total_demerits+best[1].demerits
        to_bp.via = best[0]
        to_bp.line_number = to_bp.via.line_number+1
        to_bp.fitting = best[1]
        to_bp.number = breakpoint_count
        breakpoint_count += 1


    # Starting with the last breakpoint...
    best_sequence = [ [x for x in items if isinstance(x, Breakpoint)][-1] ]

    if best_sequence[0].number is None:
        # eventually this will cause hyphenation, but for now...
        logger.debug("wrap: all wrapping options were terrible")
        logger.debug("wrap: the results were: %s", pretty_list_dump(items))
        logger.debug("wrap: %s", subsequences.dump())
        raise ValueError("all wrapping options were terrible")

    while best_sequence[0].number != 0:
        best_sequence.insert(0, best_sequence[0].via)
    logger.debug("wrap: best sequence is %s", best_sequence)

    if trace.value:
        trace.info(subsequences.trace())

    # Drop the breakpoint at the beginning
    best_sequence = best_sequence[1:]

    hboxes = [HBox()]

    spaces = best_sequence[0].fitting.spaces

    for item in items:
        if hboxes[-1].is_void() and item.discardable:
            continue

        if item==best_sequence[0]:
            if not hboxes[-1].is_void():
                hboxes.append(HBox())
            best_sequence.pop(0)
            if best_sequence:
                spaces = best_sequence[0].fitting.spaces

        elif not isinstance(item,
                Breakpoint,
                ):
            if isinstance(item, Leader):
                hboxes[-1].append(Leader(
                    glue = yex.value.Glue(
                        space = spaces.pop(0),
                        space_unit = 'sp',
                        ),
                    vertical = item.vertical,
                    ch = item.ch,
                    ))
            else:
                hboxes[-1].append(item)

    if hboxes[-1].is_void():
        hboxes = hboxes[:-1]

    logger.debug("wrap: giving us: %s", hboxes)

    result = VBox(hboxes)
    logger.debug("wrap: which gives us: %s", result)

    return result

def prep_list(doc, items):
    """
    Munge the incoming list of items slightly.

    See p99 of the TeXbook for details.

    Arguments:
        doc (`Document`): the document we're in
        items (list of `Gismo`): the incoming items

    Returns:
        a munged list, ready to wrap
    """

    for i, n in enumerate(items):
        if hasattr(n, 'source_index'):
            n.source_index = i

    if items and isinstance(items[-1], Leader):
        logger.debug("discarding glue at the end")
        items.pop()

    items.append(Breakpoint(penalty=10000))
    items.append(Penalty(10000))
    items.append(
            Leader(glue=doc[r'\parfillskip'], ch='')
            )
    items.append(Breakpoint(penalty=-10000))
    items.append(Penalty(-10000))

    return items

def pretty_list_dump(items):
    class ListDumper:
        def __init__(self, items):
            self.items = items

        def __str__(self):
            result = []

            glue = [x for x in self.items if isinstance(x, Leader)]
            if glue:
                first_glue = glue[0]
            else:
                first_glue = None

            for item in self.items:
                if hasattr(item, 'ch'):
                    result.append(item.ch)
                elif item==first_glue:
                    result.append('_')
                elif isinstance(item, Breakpoint) and item.number is None:
                    result.append('^')
                else:
                    result.append(str(item))

            return ' '.join(result)

    return ListDumper(items)

class Subsequence_Cache:
    def __init__(self, items):
        self.items = items
        self.cache = {}

    def lookup(self, left_bp, right_bp, width):

        # This may become a string key later, when we cache things
        # in sqlite3.
        key = (left_bp, right_bp)

        try:
            return self.cache[key]
        except KeyError:
            pass

        left_bp += 1

        while self.items[left_bp].discardable and left_bp<right_bp:
            left_bp += 1

        subsequence = self.items[left_bp:right_bp+1]

        found = fit_to(
                size = width,
                line = subsequence,
                )

        self.cache[key] = found

        return found

    DUMP_FORMAT = "%9s %8s %4s %4s = %6s %7s %1s %s"

    def dump(self, best=None):
        """
        Returns a representation of the cache.

        Used for debugging.

        Doesn't include all the actual widths, because it makes the
        result unreadable. You can find them out from elsewhere in the logs.
        """
        result = [
                '',
                self.DUMP_FORMAT % (
                    'from/to', 'target w', 'from', 'to', 'taken?',
                    'badness', 'd', 'items',
                    ),
                ]
        MAX_ITEMS_WIDTH = 40

        def items_to_str(items):
            for j in range(2):
                result = []
                for item in items:
                    if isinstance(item, (WordBox, CharBox)):
                        if j==0:
                            result.append(item.ch)
                        else:
                            result.append(item.ch[0])

                if j==0:
                    result = ' '.join(result)
                    if len(result)<=MAX_ITEMS_WIDTH:
                        return result
                else:
                    result = ''.join(result)
                    if len(result)>MAX_ITEMS_WIDTH-4:
                        w = (MAX_ITEMS_WIDTH//2)-2
                        result = result[:w] + '... ' + result[-w:]
                    return result

        for (left, right), fitting in sorted(self.cache.items()):
            items = items_to_str(self.items[left:right])
            width = fitting.width
            taken = ''

            from_to = f'{left}->{right}'

            bp_left = self.items[left]
            bp_right = self.items[right]

            left_repr = bp_left.number
            right_repr = bp_right.number or ''

            if bp_right.via==bp_left:
                taken = 'taken'

            width_repr = '%4.3f' % (width,)
            result.append(self.DUMP_FORMAT % (
                from_to,
                width_repr, left_repr, right_repr, taken,
                fitting.badness, fitting.decency,
                items,
                ))

        return '\n'.join(result)

    def trace(self):
        result = ['']

        bp_to_index = {}

        # TODO: p99 says that the trace will contain a "*" if an infeasible
        # breakpoint had to be chosen; find an example for testing.

        for i, thing in enumerate(self.items):
            if isinstance(thing, yex.box.Breakpoint):
                bp_to_index[thing] = i

                if thing.number:

                    follows_discretionary = (
                            i>0 and
                            isinstance(
                                self.items[i-1], yex.box.DiscretionaryBreak))

                    for k, candidate in self.cache.items():
                        (from_bp, to_bp) = k

                        if to_bp!=i:
                            continue
                        elif candidate.badness > 999999:
                            continue

                        if follows_discretionary:
                            source = r'\discretionary'
                        else:
                            source = ''

                        if follows_discretionary or i==len(self.items)-1:
                            hyphen = '-'
                        else:
                            hyphen = ''

                        result.append(
                                f'@{source} '
                                f'via @@{self.items[from_bp].number} '
                                f'b={candidate.badness} '
                                f'p={thing.penalty} '
                                f'd={candidate.demerits}'
                                )

                    k = (bp_to_index[thing.via], i)
                    if k in self.cache:
                        fitting = self.cache[k]
                        decency = f'.{fitting.decency}'
                    else:
                        decency = ''

                    if i>0 and isinstance(
                            self.items[i-1], yex.box.DiscretionaryBreak):
                        hyphen = '-'
                    else:
                        hyphen = ''

                    result.append(
                            f'@@{thing.number}: '
                            f'line {thing.line_number}{decency}{hyphen} '
                            f't={thing.total_demerits}'
                            f' -> @@{thing.via.number}'
                            )
                    result.append('')

            elif isinstance(thing, yex.box.DiscretionaryBreak):
                result[-1] += ''.join([
                    item.ch for items in [
                        thing.prebreak, thing.postbreak, thing.nobreak
                        ]
                    for item in items])

            elif result[-1]=='' and thing.ch.strip()=='':
                pass

            else:
                result[-1] += thing.ch

        return '\n'.join(result)

class Widths:
    def __init__(self, doc):
        self.doc = doc
        self.hsize = self.doc[r"\hsize"]

    def __getitem__(self, n):
        return self.hsize

class Fitting:
    def __init__(self, badness, decency, spaces, width, bp):
        self.badness = badness
        self.decency = decency
        self.spaces = spaces
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
                f'{self.spaces}]'
                )

def fit_to(size, line):
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

    width = size - sum([x.width.value for x in line
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

    return Fitting(
            badness=badness,
            decency=decency,
            spaces=result,
            width=width,
            bp=line[-1],
            )
