import logging
import yex.parse.token

logger = logging.getLogger('yex.general')

class Pushback:
    """
    Stores items from a Tokeniser which have been pushed back.

    When you're reading from a Tokeniser, you often read more than you
    actually wanted. So you can push things back into a Pushback.
    Every Document has exactly one Pushback, which lives at doc.pushback.
    Every Tokeniser keeps track of the Pushback of their Document, and
    while the Pushback has things in it, the Tokeniser will return
    those instead of its own data. Multiple Tokenisers can point
    at the same Pushback, and they usually do.

    Pushbacks also keep count of group depth.

    Attributes:
        items (list of objects): the items stored. They will be returned
            last in, first out. The next item to be returned is
            the last one in the list.

        group_depth (int): the level of nesting of groups.
    """

    def __init__(self):
        self.items = []
        self._group_depth = 0

    @property
    def group_depth(self):
        return self._group_depth

    def push(self, thing):
        """
        Pushes back a token or a character (or anything else).

        Tokenisers which point to us will see the new thing
        first, before any of its regular input.

        If the thing is a character, it will be parsed as usual
        by the Tokeniser; if it's anything else, it will simply be yielded.

        If you supply a list (not just any iterable!) the
        contents of the list will be pushed as if you'd
        pushed them individually. Multi-character strings
        work similarly.

        Pushing None does nothing.

        This method works even at end of file.

        Args:
            thing (anything): what to push.
        """
        if thing is None:
            logger.debug("%s: not pushing back eof",
                    self)
            return

        if not isinstance(thing, (list, str)):
            thing = [thing]
        elif isinstance(thing, list):
            thing = [x for x in thing if x is not None]

        if not thing:
            logger.debug("%s: nothing to push", self)
            return

        for t in thing:
            self.adjust_group_depth(t,
                    reverse=True,
                    why='on push',
                    )

        self.items.extend(reversed([c for c in thing]))

        logger.debug("%s: pushed: %s",
                self, thing)


    def pop(self):
        """
        Returns the next item.

        We don't adjust _group_depth based on the item, because this
        method is usually used by Tokenisers which want to control that
        themselves.

        Returns:
            the next item (like I just told you). If there are
            no more items, returns None. It can't return None
            in any other circumstance.
        """

        if self.items:
            result = self.items.pop()
            logger.debug("%s: popped: %s", self, repr(result))

            return result

        return None

    def adjust_group_depth(self, c, why = '', reverse=False):
        """
        Adjusts _group_depth parameter according to incoming or outgoing items.

        When a Tokeniser or a Pushback produces any item, we want to
        keep track of group nesting. This is how we do it.

        Pushbacks call this on push, but not pop. See the docstrings of
        those methods for the reasons.

        Args:
            c (any): an item which is coming or going. If the item
                is a Token, we adjust _group_depth for BeginningGroup and
                EndGroup. Otherwise, nothing happens.
            why (str): a message for logging
            reverse (bool): True if the item is being pushed back;
                False if it's being produced or popped.
        """

        if not isinstance(c, yex.parse.Token):
            return

        cat = c.category

        if cat==yex.parse.Token.BEGINNING_GROUP:
            delta = 1
        elif cat==yex.parse.Token.END_GROUP:
            delta = -1
        else:
            return

        if reverse:
            delta *= -1

        self._group_depth += delta

        where = f'{delta}'
        if delta>0:
            where = f'+{where}'

        logger.debug("%s: _group_depth %s %s; now %s",
                self, where, why, self._group_depth)

    def another(self):
        return self.__class__()

    def check_empty(self):
        """
        Does some final checks.

        You don't need to call this.

        Raises:
            ValueError: if the checks fail.
        """
        if self.items:
            raise ValueError(
                    f'{self}: there are items still on the stack: '
                    f'{self.items}'
                    )

        if self._group_depth!=0:
            raise ValueError(
                    f'{self}: group depth should be 0 on close, '
                    f'and not {self._group_depth}'
                    )

    def clear(self):
        """
        Clears the pushback of items.
        """
        if self.items:
            logger.debug("%s: clearing; dropping %s", self, self.items)
        else:
            logger.debug("%s: clearing", self)

        self.items = []

    def __repr__(self):
        result = '[pushback;%04x' % (id(self) % 0xFFFF)

        try:
            result += f';{self._group_depth}'
            if self.items:
                result += f';{self.items}'
        except:
            result += ';inchoate'

        result += ']'
        return result
