BUG_TRACKER = "https://gitlab.com/marnanel/yex/-/issues"

def t(n):
    r"""
    Returns the str() of an object plus a description of its type.

    For use in descriptions of error messages.

    Args:
        n: any object

    Returns:
        If n is exactly the string "EOF", returns "end of file".
        If n is None, returns "None".
        Otherwise, returns f"{n} (which is a {type(n)})".
    """
    if n=='EOF':
        return 'end of file'
    elif n is None:
        return 'None'
    else:
        return f'{n} (which is {n.__class__.__name__})'

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
            raise ValueError(
                    "The code tried to raise an exception "
                    f"of type {self.__class__.__name__}, "
                    "which has no form and therefore can't be raised. "
                    "Did you intend to raise one of its subclasses?")
            return

        try:
            self.message = eval(f"fr'''{self.form}'''", globals(), kwargs)

            if 'reason' in kwargs:
                self.message += f'\n{kwargs["reason"]}'

        except Exception as e:
            self.message = (
                    f"Error in error: {e}; "
                    f"form is: {self.form}; "
                    f"details are: {kwargs}"
                    )

        if kwargs.get('log', True):
            import logging
            logger = logging.getLogger('yex.general')

            logger.debug("%s: %s",
                    self.__class__.__name__,
                    self.message)

    def __getitem__(self, k):
        return self.kwargs[k]

    def __str__(self):
        if self.message is None:
            return super().__str__()
        return self.message

    def mark_as_possible_rvalue(self, name):
        self.message = self.message or 'Something went wrong.'
        self.message += '\n\n'
        self.message += (
                f'This happened while I was trying '
                f'to find a value to write into {name}. '
                f"It's possible that you intended to *read* "
                f'the value of {name} instead.'
                )

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

class RemovingNonexistentControlError(YexControlError):
    form = (
            "I can't remove control {field}, "
            "because it doesn't exist anyway."
            )

##############################

class YexParseError(YexError):
    pass

class UnknownUnitError(YexParseError):
    form = '{unit_class} does not know the unit {unit}.'

class NoUnitError(YexParseError):
    form = 'Dimens need a unit, but I found {t(problem)}.'

class ExpectedNumberError(YexParseError):
    form = 'Expected a number, but I found {t(problem)}.'

class ExpectedBoxError(YexParseError):
    form = 'Expected a box, but I found {t(problem)}.'

class LiteralControlTooLongError(YexParseError):
    form = (
            'Literal control sequences must have names of one character: '
            'yours was {name}.'
            )

class NeededBalancedGroupError(YexParseError):
    form = (
            'I needed a group with curly brackets around it, '
            'but I found {t(problem)}.'
            )

class NeededFontSetterError(YexParseError):
    form = (
            'I needed a font setter, but I found {t(problem)}.'
            )

class NeededSomethingElseError(YexParseError):
    form = (
            'I needed a {needed.__name__}, but I found {t(problem)}.'
            )

class RunawayExpansionError(YexParseError):
    form = (
            'I was expanding a macro, but the arguments went off the '
            'end of a paragraph.'
            )

class UnexpectedEOFError(YexParseError):
    form = (
            'I wasn\'t expecting the file to end just yet.'
            )

class WrongKindOfGroupError(YexParseError):
    form = (
            'I was trying to close a group with {needed}, '
            'but the most recent group was opened with {found}.'
            )

class WeirdTokenError(YexParseError):
    form = 'What should I do with {token}, which is {t(token)}?'

class WeirdDefNameError(YexParseError):
    form = (
            'Definition names must be a control sequence '
            'or an active character (not {problem.meaning})'
            )

class OuterOutOfPlaceError(YexParseError):
    form = (
            r"{problem} was defined using \outer, "
            "which means it can't be used here."
            )

class OuterInParamsError(YexParseError):
    form = "outer macros are not allowed in param lists."

class CsnameWeirdFollowingError(YexParseError):
    form = (
            r'\csname can only be followed by standard characters, '
            r'and not {t(problem)}.'
            )

class ExpectedDefError(YexParseError):
    form = r'I expected \def or similar, not {t(problem)}.'

class ParamsNotInOrderError(YexParseError):
    form = (
            "Parameters must occur in ascending order. "
            "I found {which.ch}, but I needed {param_count+1})."
            )

class ZerothParameterError(YexParseError):
    form = "Use of {name} doesn't match its definition."

class FiNotInConditionalBlockError(YexParseError):
    form = r"Can't \fi; we're not in a conditional block."

class ElseNotInConditionalBlockError(YexParseError):
    form = r"Can't \else; we're not in a conditional block."

class OrNotInCaseBlockError(YexParseError):
    form = r"Can't \or; we're not in a \case block."

class WeirdParamSymbolError(YexParseError):
    form = "Parameters can only be named with digits, not {which}."

class ExpectedButFoundError(YexParseError):
    form = 'I expected a {expected}, but found {t(found)}.'

class CantUseTokenInMode(YexParseError):
    form = "You can't use {token} in {mode}."
 
class UnitTooComplexError(YexParseError):
    form = (
            'unit "{unit}" is too complex for a literal; '
            "if you don't like this, please fix it"
            )

class NeededToHere(YexParseError):
    form = 'I needed "to" here.'

class NeededFilenameHere(YexParseError):
    form = 'I needed a filename here.'

class WeirdComparisonOperator(YexParseError):
    form = "Comparison operator must be <, =, or >, not {t(problem)}."

class NeedOpenCurlyBracketError(YexParseError):
    form = 'I needed a "{" here, and not {t(problem)}.'

class CantAssignToItemError(YexParseError):
    form = "You can't assign to {item}."

class ImproperAlphabeticConstantError(YexParseError):
    form = 'Improper alphabetic constant: {t(problem)}'

##############################

class YexValueError(YexError):
    pass

class CantAddError(YexValueError):
    form = "Can't add {t(them)} to {t(us)}."

class CantSubtractError(YexValueError):
    form = "Can't subtract {t(them)} from {t(us)}."

class CantMultiplyError(YexValueError):
    form = "You can only multiply {t(us)} by numeric values, not {t(them)}."

class CantDivideError(YexValueError):
    form = "You can only divide {t(us)} by numeric values, not {t(them)}."

class DifferentUnitClassError(YexValueError):
    form = "{t(us)} and {t(them)} are measuring different kinds of things."

class DifferentInfinityError(YexValueError):
    form = "{t(us)} and {t(them)} are infinitely different."

class ForbiddenInfinityError(YexValueError):
    form = "You can only use finite units here, not fil/fill/filll."

class NoSuchFontdimenError(YexValueError):
    form = "{fontname} only has dimens {allowed}, not {problem}."

class FontdimenIsFixedError(YexValueError):
    form = 'You can only add new dimens to a font before you use it.'

class NoOutputDriverError(YexValueError):
    form = 'No output driver found.'

class WeirdFormatError(YexValueError):
    form = 'Unknown format: {format}.'

class ParshapeNegativeError(YexValueError):
    form = r"\parshape count must be >=0, not {count}"

class WeirdRunLevelError(YexValueError):
    form = 'Unknown run level: {level}.'

class SourceHasGoneAwayError(YexValueError):
    form = 'The source has gone away now.'

class GoneBeforeTheBeginningError(YexValueError):
    form = "You have gone back before the beginning."

class IncomparableError(YexValueError):
    form = "Can't compare {left} with {right}."

class CantInitialiseError(YexValueError):
    form = "Couldn't initialise {var} with {args} for {field}"

class NamelessFontError(YexValueError):
    form = 'No name given to font.'

class ClosingOutermostModeError(YexValueError):
    form = "You can't close the outermost mode."

class UnexpectedOutermostModeError(YexValueError):
    form = '{mode} seems unexpectedly to be the outermost mode'

class UnexpectedModeError(YexValueError):
    form = 'I expected the mode to be {expected}, but it was {found}.'

class MoreGroupEndedThanBeganError(YexValueError):
    form = 'More groups ended than began!'

##############################

class YexInternalError(YexError):
    def __init__(self, *args, **kwargs):
        kwargs['reason'] = kwargs.get('reason', '') + (
                "This should never happen. Please raise a bug at\n"+
                BUG_TRACKER
                )
        super().__init__(*args, **kwargs)

class WeirdControlNameError(YexInternalError):
    form = (
            "I don't understand what you mean by naming an argument "
            '"{argname}".'
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

class ArgspecSelfError(YexInternalError):
    form = (
            "I need a 'self' parameter at the front here."
            )

class CalledAnArrayError(YexInternalError):
    form = (
            'You called an array directly. Please use get_member().'
            )

class ArrayReturnWasWeirdError(YexInternalError):
    form = (
            "Arrays must return controls with values, not {t(problem)}."
            )

class TokensWasNoneError(YexInternalError):
    form = (
            "You must supply a value for 'tokens' here."
            )

class OrdLengthWasNot1Error(YexInternalError):
    form = (
            "Expected a string of length 1 here, but someone passed in "
            "{repr(problem)}."
            )

class MismatchedMacroRecordsError(YexInternalError):
    form = (
            "A macro started and ended with different records."
            )

class SpinOnNoneError(YexInternalError):
    form = (
            '{spins} spins on None; '
            '{caller} should probably not have on_eof="none".'
            )

class ConstructorError(YexInternalError):
    form = "Create these things using the factory, not directly."

class BoxMergingError(YexInternalError):
    form = (
            "HBox.insert() merging VBoxes is only supported if "
            "where is None (i.e. at the end); "
            "if you don't like this, please fix it"
            )

class MultipleDelegatesError(YexInternalError):
    form = (
            "Expander already has a delegate; "
            "this should never happen."
            )

class AlreadyInitialisedError(YexInternalError):
    form = 'Already initialised'

class UnknownCategoryError(YexInternalError):
    form = 'Unknown category: {ch} is {category}'
