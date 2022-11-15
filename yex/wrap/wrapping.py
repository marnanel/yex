"""
Wraps paragraphs into lines.

See chapter 14 of the TeXbook for details.
"""

import yex
import yex.value
import yex.parse
from yex.wrap.fitting import Fitting
from yex.wrap.dump import pretty_list_dump
from yex.box import *
import logging

logger = logging.getLogger('yex.general')

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

        found = Fitting.fit_to(
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
