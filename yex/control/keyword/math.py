"""
Mathematical controls.

TeX has many, many controls dedicated to typesetting maths (or, if
you're American, typesetting math). Few of them are implemented,
because maths isn't a priority for yex. If you need them,
feel free to volunteer to help.
"""
from yex.control.control import Unexpandable

class Math(Unexpandable):
    horizontal = 'math'
    vertical = 'math'
    math = True

class Mathaccent(Math): pass
class Radical(Math): pass
class Displaylimits(Math): pass
class Limits(Math): pass
class Nolimits(Math): pass

class Displaystyle(Math): pass
class Textstyle(Displaystyle): pass
class Scriptstyle(Displaystyle): pass
class Scriptscriptstyle(Displaystyle): pass

class GeneralisedFraction(Math): pass
class Over(GeneralisedFraction): pass
class Atop(GeneralisedFraction): pass
class Above(GeneralisedFraction): pass
class Overwithdelims(GeneralisedFraction): pass
class Atopwithdelims(GeneralisedFraction): pass
class Abovewithdelims(GeneralisedFraction): pass

class Left_or_right(Math): pass
class Left(Left_or_right): pass
class Right(Left_or_right): pass

class Eqno(Math): pass
class Leqno(Eqno): pass

class Delimiter(Math): pass

class Mathbin(Math): pass
class Mathchar(Math): pass
class Mathchoice(Math): pass
class Mathclose(Math): pass
class Mathinner(Math): pass
class Mathop(Math): pass
class Mathopen(Math): pass
class Mathord(Math): pass
class Mathpunct(Math): pass
class Mathrel(Math): pass
class Mskip(Math): pass
class Nonscript(Math): pass

class Overline(Math): pass
class Underline(Overline): # wombling free
    pass

class A_0024(Math): # dollar
    """
    Switches inline maths mode on or off.
    """
