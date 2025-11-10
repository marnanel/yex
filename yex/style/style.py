class Style:
    r"""
    Styles, in yex, describe the state of the
    [document](yex.Document.md) before you start processing any input.

    At present, yex ships with two styles:

    - [`Bare`](yex.style.Bare.md), which is TeX and nothing else
    - [`Plain`](yex.style.Plain.md): "plain TeX", which
    is what you would get from a stock TeX installation.

    Issue:
        "Plain" is currently not working. See
        [#58](https://gitlab.com/marnanel/yex/-/issues/58).

    Eventually we will have some sort of proper caching mechanism. But even
    then, it'll be useful to have Plain hardcoded.

    You can create these styles using, for example,

    ``` shell
        python -m yex plain.tex --bare --dump > plain.json

        python -m yex.style plain.json > plain.py
    ```

    Attributes:
        CATCODES (Mapping[int,int]):
            a dict mapping codepoints to category codes. This is kept
            separate from `OTHER` because all parsing depends
            on getting the category codes correct.

        MACROS (Mapping[str,Mapping[str,Any]]):
            a dict mapping identifiers to descriptions of macros.
            The format is the same as produced by `Macro.__getstate__()`,
            except that

            - the `macro` field, which names the macro, is
            omitted if it's the same as the key of the identifier,
            with a backslash prefixed if the length is more than one.
            - the `starts_at` field is replaced by a `loc` field,
            which holds a triplet of three integers: (filename, line, column)
            where "filename" is an index into the `LOCATION_FILENAMES`
            attribute.

            This is kept separate from `OTHER` so that we don't incur
            the performance hit of recreating all the macros every time
            we start up the program.

        LOCATION_FILENAMES (Mapping[int,str]):
            a list of strings giving filenames; see `MACROS`
            above.

        OTHER (Mapping[str,Mapping[str,Any]]):
            a dict mapping strings to representations of objects,
            such that the object could be regenerated on a given Document
            by calling
            ```
                doc[key] = value
            ```
    """

    @classmethod
    def catcodes_as_dict(cls):
        import collections
        from yex.parse import Token

        result = collections.defaultdict(
                lambda: Token.OTHER,
                cls.CATCODES,
                )

        return result

    def macros(self):
        return self.MACROS

    def location_filenames(self):
        return self.LOCATION_FILENAMES

    def other(self):
        return self.OTHER

    def __repr__(self):
        return self.__class__.__name__
