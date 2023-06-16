This is the directory for testing trip tests.

They will eventually be part of the ordinary tests, but at present they're
not even reliable enough to xfail.

The extra files are from texlive's `texk/web2c/triptrap` directory.

Our design is different enough from TeX's design that some parts of the
triptest aren't relevant to us.  The only parts of the triptest that make
sense to implement is part 5 of the original:

> Compare the `TRIP.LOG` file from step 4 *[which was produced from trip.tex]*
> with the "master" `TRIP.LOG` file of step 0. (Let's hope you put that master
> file in a safe place so that it wouldn't be clobbered.) There should
> be perfect agreement between these files except in the following respects:
>
>  a)The dates and possibly the file names will naturally be different.
>
>  b)Glue settings in the displays of TEX boxes are subject to
>  system-dependent rounding, so slight deviations are permissible.
>  However, such deviations apply only to the "glue set" values that
>  appear at the end of an `\hbox` or `\vbox` line; all other numbers
>  should agree exactly, since they are computed with integer arithmetic
>  in a prescribed system-independent manner.
>
>  c)The amount of space in kerns that are marked "for accent" are,
>  similarly, subject to system-dependent rounding.
>
>  d)If you had different values for `stack_size`, `buf_size`, etc.,
>  the corresponding capacity values will be different when they
>  are printed out at the end.
>
>  e)Help messages may be different; indeed, the author encourages
>  non-English help messages in versions of TEX for people who don't
>  understand English as well as some other language.
>
>  f)The total number and length of strings at the end may well be different.
>
>  g)If your TEX uses a different memory allocation or packing scheme
>  or DVI output logic, the memory usage statistics may change.

In our case, the results won't generally be textually identical at all,
but the meaning should be the same.
