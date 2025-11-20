
We need to remove n_a_i_g. Currently it's metnioned in:

* yex/control/keyword/documentfield.py:67:class X__next_assignment_is_global(DocumentField):
* yex/control/keyword/macro.py:61:            tokens.doc.next_assignment_is_global = True
* yex/control/keyword/macro.py:207:        tokens.doc.next_assignment_is_global = True
* yex/document/group.py:91:        self.next_assignment_is_global = False
* yex/document/document.py:73:        next_assignment_is_global (bool): if True, the next
* yex/document/document.py:103:        self.next_assignment_is_global = False
* yex/document/document.py:237:        elif self.next_assignment_is_global:
* yex/document/document.py:254:                self, repr(field), index, self.next_assignment_is_global,
* yex/document/document.py:257:        self.next_assignment_is_global = False
* yex/document/document.py:604:        if self.next_assignment_is_global:
* yex/document/document.py:605:            self.next_assignment_is_global = False

The idea is to make Global check the following token, and if it's *either* a function def *or* a chardef etc, we call it with a `global=true` flag. If neither, we complain.

Thus all current tests should still pass. We should add a few for `\global` followed by something weird.
