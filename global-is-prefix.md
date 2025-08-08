We need to remove n_a_i_g. Currently it's metnioned in:

* yex/control/keyword/documentfield.py:67:class X__next_assignment_is_global(DocumentField): -- done
* yex/control/keyword/macro.py:61:            tokens.doc.next_assignment_is_global = True -- done
* yex/control/keyword/macro.py:207:        tokens.doc.next_assignment_is_global = True -- done
* yex/document/group.py:91:        self.next_assignment_is_global = False -- done
* yex/document/document.py:73:        next_assignment_is_global (bool): if True, the next -- done
* yex/document/document.py:103:        self.next_assignment_is_global = False -- done
* yex/document/document.py:237:        elif self.next_assignment_is_global: -- done
* yex/document/document.py:254:                self, repr(field), index, self.next_assignment_is_global, -- done
* yex/document/document.py:257:        self.next_assignment_is_global = False
* yex/document/document.py:604:        if self.next_assignment_is_global:  -- done
* yex/document/document.py:605:            self.next_assignment_is_global = False  -- done

The idea is to make Global check the following token, and if it's *either* a function def *or* a chardef etc, we call it with a `global=true` flag. If neither, we complain.

If global==true, we don't call `remember_restore`.

Thus all current tests should still pass. We should add a few for `\global` followed by something weird.

WHat can validly follow `\global`?

Answer: `\global` and friends are prefixes; they set flags for the next operation. But this should be handled by the expander, not in the document. We need a decorator to show what prefixes a command can validly take.

XXX We also have to account for `\globaldefs`.

ALSO: make a branch with tests from [this list](https://www.tug.org/utilities/plain/cseq.html).
