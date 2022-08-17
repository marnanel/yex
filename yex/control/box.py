"""
Box controls.

These controls create and modify boxes.

The classes implementing the boxes themselves are in `yex.box`.
"""
import logging
from yex.control.control import *
import yex.decorator
import yex.box

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
def Lastbox():
    raise NotImplementedError()

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

class C_BoxDimensions(C_Unexpandable):

    dimension = None

    def _get_box(self, tokens):
        which = yex.value.Number.from_tokens(tokens).value
        logger.debug("%s: find box number %s",
                self, which)

        result = tokens.doc.registers['box']. \
                get_directly(which, destroy = False)
        logger.debug("%s:   -- it's %s",
                self, result)

        return result

    def get_the(self, tokens):
        box = self._get_box(tokens)

        dimension = self.dimension
        logger.debug("%s:  -- looking up its %s",
                self, dimension)

        result = getattr(box, dimension)

        logger.debug("%s:    -- %s",
                self, result)

        return str(result)

    def __call__(self, tokens):
        raise yex.exception.YexError(
                f"you cannot set the {self.dimension} of a box directly"
                )

class Wd(C_BoxDimensions):
    dimension = 'width'

class Ht(C_BoxDimensions):
    dimension = 'height'

class Dp(C_BoxDimensions):
    dimension = 'depth'

##############################

class Setbox(C_Unexpandable):
    def __call__(self, tokens):
        index = yex.value.Number.from_tokens(tokens)
        tokens.eat_optional_equals()

        rvalue = tokens.next(level='executing')

        if not isinstance(rvalue, yex.box.Box):
            raise yex.exception.YexError(
                    f"this was not a box: {rvalue} {type(rvalue)}"
                    )

        tokens.doc[fr'\box{index}'] = rvalue

class Showbox(C_Unexpandable):
    def __call__(self, tokens):
        index = yex.value.Number.from_tokens(tokens)

        box = tokens.doc[fr'\copy{index}'].value

        result = box.showbox()

        print('\n'.join(result))

##############################

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
    return yex.box.Leader(glue=glue)

@yex.decorator.control(
    horizontal = 'vertical',
    vertical = True,
    )
def Vskip(glue: yex.value.Glue):
    r"""
    Adds a vertical leader.
    """
    return yex.box.Leader(glue=glue)

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

class Mark(C_Unexpandable): pass

class C_Mark(C_Unexpandable): pass
class Firstmark(C_Mark): pass
class Botmark(C_Mark): pass
class Splitfirstmark(C_Mark): pass
class Splitbotmark(C_Mark): pass
class Topmark(C_Mark): pass

class Leaders(C_Unexpandable): pass
class Cleaders(Leaders): pass
class Xleaders(Leaders): pass

class C_Unsomething(C_Unexpandable): pass
class Unpenalty(C_Unsomething): pass
class Unkern(C_Unsomething): pass
class Unskip(C_Unsomething): pass
