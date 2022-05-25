"""
Mathematical controls.

TeX has many, many controls dedicated to typesetting maths (or, if
you're American, typesetting math). Few of them are implemented,
because maths isn't a priority for yex. If you need them,
feel free to volunteer to help.
"""
from yex.control.control import C_Unexpandable

class C_Math(C_Unexpandable):
    horizontal = 'math'
    vertical = 'math'
    math = True

class Mathaccent(C_Math): pass
class Radical(C_Math): pass
class Displaylimits(C_Math): pass
class Limits(C_Math): pass
class Nolimits(C_Math): pass

class Displaystyle(C_Math): pass
class Textstyle(Displaystyle): pass
class Scriptstyle(Displaystyle): pass
class Scriptscriptstyle(Displaystyle): pass

class C_GeneralisedFraction(C_Math): pass
class Over(C_GeneralisedFraction): pass
class Atop(C_GeneralisedFraction): pass
class Above(C_GeneralisedFraction): pass
class Overwithdelims(C_GeneralisedFraction): pass
class Atopwithdelims(C_GeneralisedFraction): pass
class Abovewithdelims(C_GeneralisedFraction): pass

class C_Left_or_right(C_Math): pass
class Left(C_Left_or_right): pass
class Right(C_Left_or_right): pass

class Eqno(C_Math): pass
class Leqno(Eqno): pass

class Delimiter(C_Math): pass

class Mathbin(C_Math): pass
class Mathchar(C_Math): pass
class Mathchoice(C_Math): pass
class Mathclose(C_Math): pass
class Mathinner(C_Math): pass
class Mathop(C_Math): pass
class Mathopen(C_Math): pass
class Mathord(C_Math): pass
class Mathpunct(C_Math): pass
class Mathrel(C_Math): pass
class Mskip(C_Math): pass
class Nonscript(C_Math): pass

class Overline(C_Math): pass
class Underline(Overline): # wombling free
    pass

class A_0024(C_Math): # dollar
    """
    Switches inline maths mode on or off.
    """
