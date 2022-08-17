def t(n):
    return f'{n} (which is a {type(n)})'

class YexError(Exception):

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args)

        self.kwargs = kwargs

        if not hasattr(self, 'form'):
            return

        try:
            g = self.form.replace("'", "\\'")
            self.message = f'({self.code}) '
            self.message += eval(f"f'{g}'", globals(), kwargs)
        except Exception as e:
            self.message = (
                    f"Error in error: {e}; "
                    f"form is: {self.form}; "
                    f"details are: {kwargs}"
                    )

    def __getitem__(self, k):
        return self.kwargs[k]

    def __str__(self):
        return self.message

class ParseError(YexError):
    pass

class MacroError(YexError):
    pass

class RunawayExpansionError(ParseError):
    pass

##############################
# YexControlErrors all have codes beginning C, D, E.

class YexControlError(YexError):
    pass

class EndcsnameError(YexControlError):
    code = 'CABBAGE'
    form = r"You used an \endcsname without a preceding \csname."

##############################
# YexParseErrors all have codes beginning P, Q, R.

class YexParseError(YexError):
    pass

class UnknownUnitError(YexParseError):
    code = 'PACHIRA'
    form = '{unit_class} does not know the unit {unit}.'

class RegisterNegationError(YexParseError):
    code = 'PALAFOX'
    form = "There is no unary negation of registers."

class NoUnitError(YexParseError):
    code = 'PAMPANO'
    form = 'Dimens need a unit, not {t(problem)}.'

class ExpectedNumberError(YexParseError):
    code = 'PAPYRUS'
    form = 'Expected a number, but found {t(problem)}.'

class LiteralControlTooLongError(YexParseError):
    code = 'PAREIRA'
    form = (
            'Literal control sequences must have names of one character: '
            'yours was {name}.'
            )

##############################
# YexValueErrors all have codes beginning V, W, X, Y, Z.

class YexValueError(YexError):
    pass

class CantAddError(YexValueError):
    code = 'VATERIA'
    form = "Can't add {t(them)} to {us}."

class CantSubtractError(YexValueError):
    code = 'VELEZIA'
    form = "Can't subtract {t(them)} from {us}."

class CantMultiplyError(YexValueError):
    code = 'VERBENA'
    form = "You can only multiply %(us)s by numeric values, not {t(them)}."

class CantDivideError(YexValueError):
    code = 'VERVAIN'
    form = "You can only divide {us} by numeric values, not {t(them)}."

class DifferentUnitClassError(YexValueError):
    code = 'VANILLA'
    form = "{us} and {t(them)} are measuring different kinds of things."

class DifferentInfinityError(YexValueError):
    code = 'VARITAL'
    form = "{us} and {t(them)} are infinitely different."

class ForbiddenInfinityError(YexValueError):
    code = 'VREISEA'
    form = "You can only use finite units here, not fil/fill/filll."
