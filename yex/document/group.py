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
        ephemeral (`bool`): `True` if this group should end as soon as
            the first group inside it.
    """

    def __init__(self, doc, ephemeral=False):
        self.doc = doc
        self.restores = {}
        self.ephemeral = ephemeral

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
                yex.control.C_Parameter,
                yex.register.Register,
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

            if f=='_mode' and self.doc.mode.result is not None:
                logger.debug("%s: ended mode %s", self, self.doc.mode)

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

            self.doc.__setitem__(
                    field = f,
                    value = v,
                    from_restore = True,
                    )

        logger.debug("%s:  -- restores done.",
                self)
        self.restores = {}

    def __repr__(self):
        if self.ephemeral:
            e = ';e'
        else:
            e = ''

        return 'g;%04x%s' % (hash(self) % 0xffff, e)

class GroupOnlyForModes(Group):
    r"""
    Like Group, except it only restores `'_mode'`.

    All other changes are passed on to a delegate Group, which is
    the one previous to this Group in the groups list.

    This is for mode changes when we know we'll need to snap back
    to the previous mode.

    Attributes:
        doc (`Document`): the doc we're in
        delegate (`Group`): a Group which can handle changes that we can't.
            May be `None`, in which case such changes are ignored.
    """

    FIELDS = set(['_mode'])

    def __init__(self, doc, delegate, ephemeral=False):
        super().__init__(doc, ephemeral)
        self.delegate = delegate
        logger.debug('Will restore _mode.')

    def remember_restore(self, f, v):
        if f in self.FIELDS:
            super().remember_restore(f, v)
        elif self.delegate is not None:
            self.delegate.remember_restore(f, v)

    def __repr__(self):
        return super().__repr__()+';ofm'
