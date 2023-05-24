import yex
import logging
from yex.wrap.fitting import Fitting
from yex.util import fraction_to_str

logger = logging.getLogger('yex.general')

TEN_THOUSAND = 10000
HUNDRED_THOUSAND = 100000
MACHINE_INFINITY = 2**30-1

TOPSKIP = r'\topskip'

class Paragraphs:
    """
    A sequence of paragraphs, waiting to be broken up into pages.
    """

    def __init__(self, doc,
            produce_page,
            ):

        self.doc = doc

        self.items = []
        self.produce_page = produce_page

        self.trace = doc.get(r'\tracingpages', param_control=True)
        self.goal = doc.get(r'\vsize')
        self.maxdepth = doc.get(r'\maxdepth')

        self.total_height = None
        self.best_so_far = None
        self._must_adjust_topskip = False

        self.trace.info(
                '%% '
                f'goal height={self.goal.__repr__(show_unit=False)}, '
                f'max depth={self.maxdepth.__repr__(show_unit=False)}'
                )

        logger.debug("%s: created new Paragraphs", self)

        self._add_topskip()

    def add(self, item):

        if isinstance(item, yex.box.VBox):
            for thing in item:
                self.add(thing)
            return

        self._add_topskip()

        self.total_height += item.height

        if not self.items and item.discardable:
            logger.debug(r"%s: item is discardable, so let's do so: %s",
                    self, item)
            return

        self.items.append(item)
        self._add_topskip()

        if isinstance(item, yex.box.Penalty):
            logger.debug(r"%s: considering breaking at penalty: %s",
                    self, item)
            self._consider_breaking(
                    items = self.items,
                    penalty = item.demerits,
                    )
            return

        if len(self.items)>1 and isinstance(item, yex.box.Leader):
            if self.items[-2].discardable:
                logger.debug(r"%s: considering breaking at leader: %s",
                        self, item)
                self._consider_breaking(
                        items = self.items,
                        )
                return

            if isinstance(self.items[-2], yex.box.Kern):
                logger.debug(r"%s: considering breaking at leader: %s",
                        self, item)
                self._consider_breaking(
                        items = self.items[:-1],
                        )
                return

        logger.debug(r"%s: we can't break here: %s",
                self, item)

    def flush(self):
        logger.debug("%s: flushing", self)

        previous = None
        while self.items!=previous:
            self._consider_breaking(self.items)
            previous = self.items

        if self.best_so_far is not None:
            self.produce_page(self.items)

        self.items = []
        logger.debug("%s: flushed", self)

    def _consider_breaking(self, items, penalty=0):
        r"""
        Decides whether to break the page at a particular place.
        If we decide to break, calls self.produce_page.
        If we decide not to break, this is a no-op.

        The TeXbook and tex.web appear to be at odds on the algorithm here.
        The TeXbook (p111) has

            c = p, if b<∞ and p≤-10000 and q<10000
            c = b+p+q, if b<10000 and (-10000<p<10000) and q<10000
            c = 10000, if b=10000 and (-10000<p<10000) and q<10000
            c = ∞, if (b=∞ or q≥10000) and p≤-10000

        with no fallback case.

        But tex.web (starting at line 19553) has

            if pi<inf_penalty then
                [ it sets b:=badness here ]
                if b<awful_bad then
                  if pi<=eject_penalty then c:=pi
                  else  if b<inf_bad then c:=b+pi+insert_penalties
                    else c:=deplorable
                else c:=b;
                if insert_penalties>=10000 then c:=awful_bad;

        where "pi" is the local name for p (rather than 3.14...),
        awful_bad is machine infinity (2**30-1), inf_bad is
        ten thousand, eject_penalty is minus ten thousand,
        and deplorable is a hundred thousand.
        So we're going with tex.web.

        Args:
            items (list of Gismo): we are considering whether to break
                after this list. It should be a prefix of self.items.
            penalty (int): the penalty for breaking here. Usually zero,
                but if we break at a Penalty, we take this value from it.

        Returns:
            None.
        """
        badness = self._calculate_badness(items)
        insert_penalties = 0

        if insert_penalties>=TEN_THOUSAND:
            cost = MACHINE_INFINITY
        elif badness==MACHINE_INFINITY:
            cost = MACHINE_INFINITY
        elif penalty<=-TEN_THOUSAND:
            cost = penalty
        elif badness<TEN_THOUSAND:
            cost = badness+penalty+insert_penalties
        else:
            cost = HUNDRED_THOUSAND

        found_best = self.best_so_far is None or cost<self.best_so_far[0]

        def maybe_infinite(n):
            if n==MACHINE_INFINITY:
                return '*'
            else:
                return str(n)

        def maybe_hash():
            if found_best:
                return '#'
            else:
                return ''

        self.trace.info(
                '% '
                f't={fraction_to_str(self.total_height.value, 16)} '
                f'g={fraction_to_str(self.goal.value, 16)} '
                f'b={maybe_infinite(badness)} '
                f'p={penalty} '
                f'c={maybe_infinite(cost)}'
                f'{maybe_hash()}'
                )

        if not found_best:
            logger.debug("%s: cost is %d; we've seen better", self, cost)
            return

        self.best_so_far = (cost, len(items))
        logger.debug("%s: cost is the best so far: %s",
                self, self.best_so_far)

        if cost==MACHINE_INFINITY or penalty<=-TEN_THOUSAND:
            logger.debug("%s:     -- let's use this", self)
            self.produce_page(self.items[:len(items)])
            self.items = self.items[len(items)+1:]
            self.best_so_far = None
            self._add_topskip()

    def _calculate_badness(self, items):
        if self.total_height>self.goal:
            return MACHINE_INFINITY

        # XXX What is page_shrink?

        fitting = Fitting.fit_to(
                size = self.goal,
                line = items,
                horizontal = False,
                )

        if fitting.is_infinite:
            return MACHINE_INFINITY
        else:
            return fitting.badness

    def is_void(self):
        return len(self.items)==0

    def _add_topskip(self):
        r"""
        Add the "topskip" glue to the top of the page.

        This is based on the height of the first item. See p113 of
        the TeXbook for the algorithm.

        This should be called only when the start of the list changes
        (other than when this function itself changes it).
        """

        if not self.items:
            topskip = yex.box.Leader(
                doc=self.doc,
                glue=TOPSKIP,
                vertical=True,
                )

            self.items = [topskip]
            self._must_adjust_topskip = True
            self.total_height = topskip.height

            self._consider_breaking(items=self.items)

        elif self._must_adjust_topskip and len(self.items)>1:

            self._must_adjust_topskip = False

            topskip = self.items[0]
            first_item = self.items[1]
            first_item_height = first_item.height + first_item.depth

            if first_item_height>=topskip.space:
                new_leader_space = yex.value.Dimen()
            else:
                new_leader_space = topskip.space-first_item_height

            logger.debug((r"%s: replacing existing topskip %s of height %s, "
                "with new topskip of height %s, "
                "before item %s with height %s"),
                self, topskip, topskip.space,
                new_leader_space,
                first_item, first_item_height)

            self.items[0] = yex.box.Leader(
                    space = new_leader_space,
                    shrink = topskip.shrink,
                    stretch = topskip.stretch,
                    name = TOPSKIP,
                    )

            self.total_height += new_leader_space - topskip.height

            logger.debug((
                r"%s: added new topskip %s of height %s; "
                "total_height is now %s"),
                self, self.items[0], new_leader_space, self.total_height)

    def __len__(self):
        if self.items:
            return len(self.items)

        return 0

    def __getitem__(self, n):
        if self.items:
            return self.items[n]

        raise IndexError(n)

    def __repr__(self):
        result = f'[Paragraphs;len={len(self.items)}]'

        return result
