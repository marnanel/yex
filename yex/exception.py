def t(n):
    r"""
    Returns the str() of an object plus a description of its type.

    For use in descriptions of error messages.

    Args:
        n: any object

    Returns:
        If n is exactly the string "EOF", returns "end of file".
        Otherwise, returns f"{n} (which is a {type(n)})".
    """
    if n=='EOF':
        return 'end of file'
    else:
        return f'{n} (which is a {n.__class__.__name__})'

class YexError(Exception):

    """
    Something that went wrong.

    Attributes:
        form: the message displayed to the user. This can contain variables
            which will be substituted from the kwargs of the constructor.
            It may not contain three apostrophes in a row. I would check
            for that, but I trust you not to be silly.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args)

        self.kwargs = kwargs

        if not hasattr(self, 'form'):
            self.message = None
            return

        try:
            self.message = eval(f"fr'''{self.form}'''", globals(), kwargs)
        except Exception as e:
            self.message = (
                    f"Error in error: {e}; "
                    f"form is: {self.form}; "
                    f"details are: {kwargs}"
                    )

    def __getitem__(self, k):
        return self.kwargs[k]

    def __str__(self):
        if self.message is None:
            return super().__str__()
        return self.message

class ParseError(YexError):
    pass

class MacroError(YexError):
    pass

class RunawayExpansionError(ParseError):
    pass

##############################

class YexControlError(YexError):
    pass

class EndcsnameError(YexControlError):
    form = r"You used an \endcsname without a preceding \csname."

# I would just like to say that "\the" was a daft name for a major control

class TheUnknownError(YexControlError):
    form = r"\the cannot define {subject} because it doesn't exist."

class TheNotFoundError(YexControlError):
    form = r"\the found no answer for {subject}."

class LetInvalidLhsError(YexControlError):
    form = (
            r"\{name} must be followed by Control or Active, "
            r"and not {t(subject)}."
            )

##############################

class YexParseError(YexError):
    pass

class UnknownUnitError(YexParseError):
    form = '{unit_class} does not know the unit {unit}.'

class RegisterNegationError(YexParseError):
    form = "There is no unary negation of registers."

class NoUnitError(YexParseError):
    form = 'Dimens need a unit, but I found {t(problem)}.'

class ExpectedNumberError(YexParseError):
    form = 'Expected a number, but I found {t(problem)}.'

class LiteralControlTooLongError(YexParseError):
    form = (
            'Literal control sequences must have names of one character: '
            'yours was {name}.'
            )

class NeededSomethingElseError(YexParseError):
    form = (
            'I needed a {needed.__name__}, but I found {t(problem)}.'
            )

##############################

class YexValueError(YexError):
    pass

class CantAddError(YexValueError):
    form = "Can't add {t(them)} to {us}."

class CantSubtractError(YexValueError):
    form = "Can't subtract {t(them)} from {us}."

class CantMultiplyError(YexValueError):
    form = "You can only multiply {us} by numeric values, not {t(them)}."

class CantDivideError(YexValueError):
    form = "You can only divide {us} by numeric values, not {t(them)}."

class DifferentUnitClassError(YexValueError):
    form = "{us} and {t(them)} are measuring different kinds of things."

class DifferentInfinityError(YexValueError):
    form = "{us} and {t(them)} are infinitely different."

class ForbiddenInfinityError(YexValueError):
    form = "You can only use finite units here, not fil/fill/filll."

##############################

class YexInternalError(YexError):
    pass

class WeirdControlNameError(YexInternalError):
    form = (
            "I don't understand what you mean by naming an argument"
            '{argname} on {control}.'
            )

class WeirdControlAnnotationError(YexInternalError):
    form = (
            "I don't understand the annotation {annotation} "
            'on {control}, argument {arg}.'
            )

class CannotSetError(YexInternalError):
    form = (
            "Tried to set {field} to {value}, but {problem}."
            )

class CannotGetError(YexInternalError):
    form = (
            "Tried to get {field}, but {problem}."
            )
