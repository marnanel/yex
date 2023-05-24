from yex.decorator import control
import yex
import roman

def _str_to_tokens(where, s):
    return [
            # All tokens returned here are Other, per the TeXbook p40
            yex.parse.Other(
                ch = c,
                location = where,
                )
            for c in s
            ]

@control()
def Number(where: yex.parse.Location, n: int):
    return _str_to_tokens(where, str(n))

@control()
def Romannumeral(where: yex.parse.Location, n: int):
    return _str_to_tokens(where, roman.toRoman(n).lower())
