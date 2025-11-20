import yex.logging
import yex
from typing import Self, Mapping, Any, Union

ASSIGNMENT_LOG_RECORD = "%s %-8s = %s"

logger = yex.logging.getLogger('document')

class Group:
    r"""
    A group, in the TeX sense.

    Created by `{` or
    [`\begingroup`](yex.control.keyword.Begingroup.md), and ended by `}` or
    [`\endgroup`](yex.control.keyword.Endgroup.md).  When the group ends,
    all assignments (except global assignments) will be undone.

    Attributes:
      doc: the [document](yex.Document.md) we belong to
      restores (Mapping[str, Any]): element values to restore when the group ends.
      from_begingroup: True if this group was created with a
        `\begingroup` command; False if it was created by a `{`;
        None if it was generated in some other way.
    """

    def __init__(self,
                 doc: 'yex.Document',
                 from_begingroup:Union[bool,None]=None):
        self.doc = doc
        self.restores = {}
        self.from_begingroup = from_begingroup

    def remember_restore(self,
                         f: str,
                         v: Any,
                         ) -> None:
        r"""
        Stores a record that we've assigned something to `self.doc[f]`
        which replaced its old value, `v`. Then we'll know
        to do `self.doc[f]=v` later, when we reach the end of
        this group.

        If multiple assignments are made to the same element in the
        same group, we only record the first: that's all we need to know to
        restore the value, and the others will be inaccurate anyway.

        Ignores assignments to
        [`\inputlineno`](yex.control.keyword.Inputlineno.md),
        since attempting to restore the
        previous line number would give unexpected results.

        This method is not called "record_restore" because people might
        interpret "record" as a noun.

        Args:
            f: the fieldname of the element
            v: the value the element had before the assignment
        """
        if f in (r'\inputlineno', ):
            # that makes no sense
            return

        if self.doc.globaldefs.is_global:
            # global assignment, so we won't be undoing it
            # at the end of the group
            return

        if f in self.restores:
            logger.debug(
                    "Redefinition of %s; ignored for remembers", f)
            return
        elif self.doc.globaldefs.is_global:
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

    def run_restores(self) -> None:
        """
        Carries out each restore recorded by `remember_restore`.

        The restores happen in no particular order.
        """
        logger.debug("%s: beginning restores: %s",
                self, self.restores)

        self.doc.globaldefs.unlock_global(
                expecting_zero = True,
                )

        for f, v in self.restores.items():

            if f=='_mode':
                logger.debug("%s: ended mode %s", self, self.doc.mode)

                self.doc.mode.close()

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
