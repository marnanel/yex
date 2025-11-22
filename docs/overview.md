# What happens inside yex

This is what happens when you run yex on a
<span class="tex">T<i>e</i>Χ</span> document:

Firstly, we create a [Document](ref/yex.Document.md) object.
This contains the system's state. It's passive: the other parts of the system
act upon it.

Next, we create a [parser](ref/yex.parse.Parser.md). This reads the
`.tex` file off disk, and turns it into a series of tokens.

Inside the Document object, there is a
[set of controls](ref/yex.control.ControlsTable.md),
each of which maps to a handler.
If the parser sees the names of any of these controls,
it will run the handler and parse the results.

The Document object also contains a [Mode](ref/yex.mode.Mode.md) object,
which receives all the finished work from the parser.
The Mode does all the work of putting the finished results into
[boxes](ref/yex.box.Box.md), working out where those boxes should go
on the page, and doing [wordwrap](ref/yex.wrap.wrap.md).
It stores all its results back into the Document.

Finally, an [output driver](ref/yex.output.Output.md) writes the
finished results to to a file of the correct format.

## Want to know more? Have a look at these pages:
- [Documents, where we store the state](ref/yex.Document.md)
- [Modes, which do the real work](ref/yex.mode.Mode.md)
- [Controls, which are stored procedures](ref/yex.control.Control.md)
