import logging
import yex

ASSIGNMENT_LOG_RECORD = "%s %-8s = %s"

logger = logging.getLogger('yex.general')

class Group:
    r"""
    A group, in the TeX sense.

    Created by ``{`` or ``\begingroup``, and ended by
    ``}`` or ``\endgroup``.  When the group ends, all assignments
    (except global assignments) will be undone.

    Attributes:
        doc (`Document`): the doc we're in
        restores (dict mapping `str` to arbitrary types): element values to
            restore when the group ends.
        from_begingroup (`bool`): `True` if this group was created with a
            ``\begingroup`` command; `False` if it was created by a ``{``;
            `None` if it was generated in some other way.
    """

    def __init__(self, doc, from_begingroup=None):
        self.doc = doc
        self.restores = {}
        self.from_begingroup = from_begingroup

    def remember_restore(self, f, v):
        r"""
        Stores `f` and `v` so we can do ``self.doc[f]=v`` later.

        If multiple assignments are made to the same element in the
        same group, we only record the first: that's all we need to know to
        restore the value, and the others will be inaccurate anyway.

        Ignores ``f="\inputlineno"``, since attempting to restore the
        previous line number would give unexpected results.

        This method is not called "record_restore" because people might
        interpret "record" as a noun.

        Args:
            f (`str`): the fieldname of the element
            v (arbitrary): the value the element had before the assignment

        Raises:
            None.

        Returns:
            `None`
        """
        if f in (r'\inputlineno', ):
            # that makes no sense
            return

        if f in self.restores:
            logger.debug(
                    "Redefinition of %s; ignored for remembers", f)
            return

        if isinstance(v, (
                yex.control.Parameter,
                yex.control.Register,
                )):
            logger.debug('dereferencing old value of %s: %s -> %s',
                    f, v, v.value)
            v = v.value

        logger.debug(
                ASSIGNMENT_LOG_RECORD,
                '*', f, repr(v))
        self.restores[f] = v

    def run_restores(self):
        """
        Carries out each restore recorded by `remember_restore`.

        The restores happen in no particular order.

        Raises:
            None.

        Returns:
            `None`
        """
        logger.debug("%s: beginning restores: %s",
                self, self.restores)

        self.next_assignment_is_global = False
        for f, v in self.restores.items():

            if f=='_mode':
                logger.debug("%s: ended mode %s", self, self.doc.mode)

                self.doc.mode.close()

                """
                if self.doc.mode.is_inner:
                    logger.debug(
                            "%s: not passing result up, because it's inner",
                            self)
                else:
                    # About to restore a previous mode; this mode is
                    # finished, so send its result to its parent.

                    logger.debug("%s:   -- result was %s", self,
                            self.doc.mode.result)

                    logger.debug("%s:   -- passing to previous mode, %s",
                        self, v)

                    v.append(item=self.doc.mode.result)

                self.doc.mode.list = []
                """

            self.doc.__setitem__(
                    field = f,
                    value = v,
                    from_restore = True,
                    )

        logger.debug("%s:  -- restores done.",
                self)
        self.restores = {}

    def __repr__(self):
        return 'g;%04x' % (hash(self) % 0xffff)
