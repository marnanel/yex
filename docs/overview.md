# What happens when you run yex

Let's consider a simple document, `trivial.tex`:

```tex
b\def\m{an}\m\m a\bye
```

Running this through TeX produces a document containing the single word `banana`:

* the letter `b` represents itself;
* then we define the macro `\m` to produces the letters `an`
* then we call that macro twice, giving `anan`
* then we have an `a` representing itself;
* then we call `\bye`, which is the TeX primitive to end a document.

What happens when we call `yex trivial.tex`?

## Commandline handling

The `yex` script is a wrapper for the Python function `yex.__main__.main()`. That function parses the commandline using `argparse`, and puts the result in a global variable called `args`. Then it calls `run()`.

`run()` then

* sets up [logging](logging)
* creates a [Document](document)
* because of the commandline, opens `trivial.tex` for reading
* calls the main yex function, `yex()`, with arguments based on all that's gone before.

# The yex() function, aka `yex.put.put`

From here on, we're into code which is used in every use of yex, whether it's as a library or from the commandline.

`yex()` is the toplevel yex package, called as a function, which is an alias for `yex.put.put`. It serves as a general interface to yex.

The caller has passed us `doc` (a Document), `source` (some kind of source of characters), and `target` (an Output), along with some less important args. The `doc` Document automatically creates a `[Mode](Mode)`.

We then:

* create an [`Expander`](Expander) to parse the document;
* create an [`Output`](Output) to receive it. Because `run()` passed in only a filename, it calls the factory function `Output.driver_for()` to create an `Output` of the correct subclass;
* iterate over the Expander, feeding everything it produces into the Document's Mode.

## Expanding

When we created the Expander, we passed it the file handle open on `trivial.tex`. The Expander automatically created a [`Tokeniser`](Tokeniser), and passed the handle on to it. The Tokeniser creates a `FileSource`, a simple wrapper to count lines and make sure all inputs work similarly.

The Tokeniser reads the first character, which is `b`, and hands a [`Token`](Token) back to the Expander, representing `b`. This Token is of TeX's type 11, LETTER; like all types of token, yex represents it by a subclass of `Token`, in this case `Letter`. The Expander has nothing to change, so it hands the Token back to `put()`.

Until this point, we've been in Vertical mode, so the Document's mode object is an instance of `yex.mode.Vertical`. `put()` hands the new Token to Vertical, which knows that a Letter requires a switch to Horizontal mode.

But we don't switch yet, because before the new Horizontal mode can handle the `b`, we must run an `\indent` in order to indent the new paragraph. Rather than try to do both jobs at once, we put them both off until the future. The Document object has a stack, implemented by the [`Pushback`](Pushback) class, so we push the `b` there, followed by a new [`Control`](Control) object.

Control objects represent TeX's controls, which are commands to the typesetter. This particular Control object is a [`yex.control.keyword.Indent`](Indent). The Mode's work is done for the moment, so we return, and `put()`'s look goes round again.

This time, the Tokeniser finds that the stack isn't empty, so it doesn't bother reading any new characters. It passes the Indent control back out to `put()`, which hands it to the Vertical mode, which runs it by calling it.

This is when we switch to horizontal mode. The Indent tells the Document to change the mode, so the Document sets its mode field to a new instance of yex.mode.Horizontal.

...

## Saving

Back in `yex.put.put()` we call `doc.save()`.

....9
