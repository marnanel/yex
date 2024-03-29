"""
Box controls.

These controls create and modify boxes.

The classes implementing the boxes themselves are in `yex.box`.
"""
import logging
from yex.control.control import Unexpandable
from yex.control.keyword.array import Array
import yex.decorator
import yex

logger = logging.getLogger('yex.general')

@yex.decorator.control()
def Hbox(tokens):
    return yex.box.HBox.from_tokens(tokens)

@yex.decorator.control()
def Vbox(tokens):
    return yex.box.VBox.from_tokens(tokens)

@yex.decorator.control()
def Vtop(tokens):
    return yex.box.VtopBox.from_tokens(tokens)

@yex.decorator.control()
def Vsplit():
    raise NotImplementedError()

@yex.decorator.control()
def Vcenter():
    raise NotImplementedError()

@yex.decorator.control()
def Lastbox(doc):

    if not doc.mode.list:
        logger.debug("lastbox: doc.mode.list is empty; returning nothing")
    elif not isinstance(doc.mode.list[-1], yex.box.Box):
        logger.debug((
            "lastbox: last element of doc.mode.list is %s, "
            "which is not a box; returning nothing"),
            doc.mode.list[-1])
    else:
        result = doc.mode.list.pop()
        return result

##############################

@yex.decorator.control(
        vertical = False,
        horizontal = True,
        math = True,
        )
def Raise(distance: yex.value.Dimen, target: yex.box.HBox):
    target.shifted_by = -distance
    return target

@yex.decorator.control(
        vertical = False,
        horizontal = True,
        math = True,
        )
def Lower(distance: yex.value.Dimen, target: yex.box.HBox):
    target.shifted_by = distance
    return target

@yex.decorator.control(
        vertical = True,
        horizontal = False,
        math = False,
        )
def Moveleft(distance: yex.value.Dimen, target: yex.box.VBox):
    target.shifted_by = -distance
    return target

@yex.decorator.control(
        vertical = True,
        horizontal = False,
        math = False,
        )
def Moveright(distance: yex.value.Dimen, target: yex.box.VBox):
    target.shifted_by = distance
    return target

##############################

class BoxDimensions(Array):

    dimension = None # override in subclass

    def get_directly(self, index):
        box = self.doc.controls[r'\copy'].get_element(index).value

        logger.debug("%s:  -- looking up its %s",
                self, self.dimension)

        result = getattr(box, self.dimension)

        logger.debug("%s:    -- %s",
                self, result)

        return result

    def get_type(self):
        return yex.value.Dimen

class Wd(BoxDimensions):
    dimension = 'width'

class Ht(BoxDimensions):
    dimension = 'height'

class Dp(BoxDimensions):
    dimension = 'depth'

##############################

@yex.decorator.control()
def Setbox(tokens, index: yex.value.Number):

    tokens.eat_optional_char('=')

    rvalue = tokens.next(level='executing')

    if not isinstance(rvalue, yex.box.Box):
        raise yex.exception.NeededSomethingElseError(
                needed = yex.box.Box,
                problem = rvalue,
                )

    tokens.doc[fr'\box{index}'] = rvalue

@yex.decorator.control()
def Showbox(doc, index: yex.value.Number):

    box = doc[fr'\copy{index}']

    result = box.showbox()

    print('\n'.join(result))

@yex.decorator.control(
    horizontal = 'vertical',
    vertical = True,
        )
def Hrule(tokens):
    """
    Adds a horizontal rule.

    See p219 of the TeXbook for the syntax rules.
    """
    return yex.box.Rule.from_tokens(tokens, is_horizontal=True)

@yex.decorator.control(
    horizontal = 'vertical',
    vertical = True,
        )
def Vrule(tokens):
    """
    Adds a vertical rule.

    See p219 of the TeXbook for the syntax rules.
    """
    return yex.box.Rule.from_tokens(tokens, is_horizontal=False)

##############################

@yex.decorator.control(
    vertical = False,
    horizontal = True,
    math = True,
    )
def Hskip(glue: yex.value.Glue):
    r"""
    Adds a horizontal leader.
    """
    return yex.box.Leader(
            glue=glue,
            vertical=False,
            )

@yex.decorator.control(
    horizontal = 'vertical',
    vertical = True,
    )
def Vskip(glue: yex.value.Glue):
    r"""
    Adds a vertical leader.
    """
    return yex.box.Leader(
            glue=glue,
            vertical=True,
            )

##############################

@yex.decorator.control(
    vertical = False,
    horizontal = True,
    math = True,
    )
def Hfil():
    """
    Skips horizontally by zero, but with infinite stretchability.
    """
    glue = yex.value.Glue(space=0, stretch=1, stretch_unit='fil')
    return yex.box.Leader(glue=glue)

@yex.decorator.control(
    math = False,
    )
def Hfill():
    """
    Skips horizontally by zero, but with more infinite stretchability.
    """
    glue = yex.value.Glue(space=0,
            stretch=1, stretch_unit='fill',
            )
    return yex.box.Leader(glue=glue)

@yex.decorator.control(
        )
def Hfilll():
    r"""
    Skips horizontally by zero, but with even more infinite stretchability.

    (TeXbook p72: "TeX does not provide a '\vfilll' primitive, since the
    use of this highest infinity is not encouraged.")
    """
    glue = yex.value.Glue(space=0,
            stretch=1, stretch_unit='filll',
            )
    return yex.box.Leader(glue=glue)

@yex.decorator.control(
    )
def Hss():
    r"""
    Skips horizontally by zero, but with more infinite stretchability.
    """
    glue = yex.value.Glue(space=0,
            stretch=1, stretch_unit='fil',
            shrink=1, shrink_unit='fil',
            )
    return yex.box.Leader(glue=glue)

@yex.decorator.control(
    )
def Hfilneg():
    r"""
    Cancels the stretchability of a previous \hfil.
    """
    glue = yex.value.Glue(space=0,
            stretch=-1, stretch_unit='fil',
            )
    return yex.box.Leader(glue=glue)

@yex.decorator.control(
    horizontal = 'vertical',
    vertical = True,
    )
def Vfil():
    r"""
    Skips vertically by zero, but with infinite stretchability.
    """
    glue = yex.value.Glue(space=0,
            stretch=1, stretch_unit='fil',
            )
    return yex.box.Leader(glue=glue)

@yex.decorator.control(
    horizontal = 'vertical',
    vertical = True,
    )
def Vfill():
    r"""
    Skips vertically by zero, but with more infinite stretchability.
    """
    glue = yex.value.Glue(space=0,
            stretch=1, stretch_unit='fill',
            )
    return yex.box.Leader(glue=glue)

@yex.decorator.control(
    horizontal = 'vertical',
    vertical = True,
    )
def Vss():
    r"""
    Skips vertically by zero, but with infinite stretchability and
    shrinkability.
    """
    glue = yex.value.Glue(space=0,
            stretch=1, stretch_unit='fil',
            shrink=1, shrink_unit='fil',
            )
    return yex.box.Leader(glue=glue)

@yex.decorator.control(
    horizontal = 'vertical',
    vertical = True,
    )
def Vfilneg():
    r"""
    Cancels the stretchability of a previous \vfil.
    """
    glue = yex.value.Glue(space=0,
            stretch=-1, stretch_unit='fil',
            )
    return yex.box.Leader(glue=glue)

##############################

class Mark(Unexpandable): pass

class Mark(Unexpandable): pass
class Firstmark(Mark): pass
class Botmark(Mark): pass
class Splitfirstmark(Mark): pass
class Splitbotmark(Mark): pass
class Topmark(Mark): pass

class Leaders(Unexpandable): pass
class Cleaders(Leaders): pass
class Xleaders(Leaders): pass

class Unsomething(Unexpandable): pass
class Unpenalty(Unsomething): pass
class Unkern(Unsomething): pass
class Unskip(Unsomething): pass
