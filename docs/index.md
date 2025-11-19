yex
===

**yex is a typesetter.** It's built to behave like Donald Knuth's
<span class="tex">T<i>e</i>X</span>
typesetter, and many
<span class="tex">T<i>e</i>X</span>
documents are quite acceptable to yex. But yex is written in
Python, and it can easily be extended to do other things.

It won't be useful for typesetting ordinary documents as yet.
But I encourage you to help fix bugs.

The biggest issues we're solving are:

- *`plain.tex` does not parse* ([issue #58](https://gitlab.com/marnanel/yex/-/issues/58)).
  Without this stylesheet, yex is unusable for ordinary work.
- *Some controls are still unimplemented*
([see label](https://gitlab.com/marnanel/yex/-/issues?label_name%5B%5D=unimplemented%20control)).
- *Tests should be as rigorous as they can be*; in particular, we need tests based on
every rule in [David Bausum's *TeX Primitive Control Sequences*](https://www.tug.org/utilities/plain/cseq.html).
See [issue #118](https://gitlab.com/marnanel/yex/-/issues/118).

You can read [an overview of the codebase](overview.md) if you're
interested in getting involved.
