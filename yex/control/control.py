import yex.logging
import yex.exception
from typing import List, Any, Union, Tuple, Type, Self

logger = yex.logging.getLogger('control')

class Control:
    r"""
    Controls are callable procedures. They live within
    a [ControlsTable](yex.control.ControlsTable.md),
    within a [document](yex.Document.md).

    Each `yex.control.Control` is usually referred to by at least one
    [yex.parse.Control](yex.parse.Token.md) token
    object in a given [document](yex.Document.md).
    *But those objects are symbols, and these are procedures*;
    don't get them confused.

    # Some subclasses of Control:

    The subclasses which are most important to understand are
    nearest to the top of this list.

    - Expandable: a control which expands into tokens.
        For example, all [macros](yex.control.Macro.md) are expandables.
        They have no side-effects; they simply expand.
    - Unexpandable: a built-in control which does something
        other than expanding. For example,
        [Hrule](yex.control.keyword.Hrule.md)
        inserts a horizontal rule.
    - [Parameter](yex.control.Parameter.md): an Unexpandable which
        has a value. For example, the value of
        [Year](yex.control.keyword.Year.md)
        is the number of the current year in the Common Era.
    - [Array](yex.control.Array.md): a control containing
        multiple values. For example, `\count`, which contains
        the values `\count0`, `\count1`, and so on.
    - [Register](yex.control.Register.md): any of the values
        which live in an array. For example, `\count1`.
    - [Macro](yex.control.Macro.md): a control created by the user
        using the `\def` control, as a subroutine.
    - [Fontsetter](yex.control.Fontsetter.md): a control created
        by the user using the `\font` control. When you call it,
        it changes the current font.
    - [Documentfield](yex.control.Documentfield.md): a parameter control
        which refers to a field in the Document. You don't really
        need to know about these.

    You can implement a new control subclass by subclassing Expandable or
    Unexpandable. But it's generally easier to use
    [the @control decorator](yex.decorator.control.md) on a function.

    # `yex.control` vs `yex.control.keyword`

    The package `yex.control` contains classes which help to make controls,
    as in the list above. The subclasses which actually represent TeX keywords live in
    `yex.control.keyword`.

    # About class identifiers

    TeX controls are named in all lowercase, with a leading backslash,
    thus: `\kern`. But we can't represent the backslash in a Python identifier,
    and Python classes traditionally have names in titlecase. So the class
    for `\kern` is [Kern](yex.control.keyword.Kern.md).

    Because there are some funky kinds of control out there, there
    are a few more ways of naming controls:

    - a class whose name begins `X_` represents a TeX control with
      the same name, lowercased, with the `X_` stripped.
    - a class whose name is `A_` followed by four hex digits
      giving a Unicode codepoint represents the TeX control whose name
      consists only of that character.
      This is useful for active characters.
    - a class whose name is `S_` followed by four hex digits
      giving a Unicode codepoint represents the TeX control whose name
      consists only of a backslash followed by that character.
     """

    even_if_not_expanding: bool = False
    r"""
    Whether this control should be executed even when the parser isn't
    executing. There are only a very few of these.

    TeXbook:
        215
    """

    is_queryable: bool = False
    r"""
    Whether this control behaves differently when it's the target
    of an assignment (often known as an "lvalue"). For this behaviour,
    you can call the `query()` method.
    """

    conditional: bool = False
    r"""
    Whether this control affects conditional execution: \if, \else,
    and so on.
    """

    is_array: bool = False
    r"""
    Whether this control is an array, where you can look up entries
    by an index number. See [yex.control.Array](yex.control.Array.md).
    """

    name: str = None
    r"""
    The name of the control. If you supply None to the constructor,
    this will be initialised with the name of the control class,
    lowercased. For example, `Year` will have `name=="year"`.
    """

    from_human: bool = True
    r"""
    False if yex itself inserted this control;
    True if it was human-generated. The only current case where this
    is False is the automatic `\indent` at the start of a paragraph.
    """

    is_long: bool = False
    r"""
    Whether this control is a macro whose arguments can include `\par`.
    """

    is_outer: bool = False
    r"""
    Whether this control is a macro which can't be used inside other macros.
    (This is an oversimplification; see the TeXbook for the full details.)

    TeXbook:
        p205
    """

    doc: Union['yex.Document', None] = None
    r"""
    The document we belong to.
    """

    def __init__(self,
                 is_long: bool = False,
                 is_outer: bool = False,
                 from_human: bool = True,
                 name: Union[str, None] = None,
                 doc: Union['yex.Document', None] = None,
                 *args, **kwargs):

        self.is_long = is_long
        self.is_outer = is_outer
        self.from_human = from_human
        self.doc = doc

        if name is None:
            self.name = self.__class__.__name__.lower()
        else:
            self.name = name

    @property
    def value(self) -> Any:
        """
        Some controls have values. For example, the value of
        `[Year](yex.control.Year.md)` is the current year
        in the Common Era.

        The type of the value can be anything at all.
        If a control has no other interesting value to give,
        then its value should be itself.

        Some values can be set; if you attempt to set a value which
        can't be set, you will get AttributeError: this is the same
        behaviour as with Python properties.

        The getter/setter behaviour is implemented under the bonnet
        by the methods `_get_value()` and `_set_value()`. This is
        because Python gets rather baroque about inheritance and
        properties.
        """
        return self._get_value()

    @value.setter
    def value(self, v: Any):
        self._set_value(v)

    def _get_value(self) -> Any:
        return self

    def _set_value(self, v) -> None:
        raise AttributeError(f"{self}.value has no setter")

    @property
    def identifier(self) -> str:
        """
        A good string to use for looking up this control in a document.

        In practice, it could be stored under a different string as well,
        or instead, or it might not be stored at all. But this is often
        a reasonable shot.
        """
        return fr'\{self.name}'

    def __call__(self, *args, **kwargs) -> Any:
        """
        Run the procedure.
        """
        raise NotImplementedError()

    def __str__(self):
        return fr'\{self.name}'

    def __repr__(self):
        return fr'[\{self.name}]'

    @classmethod
    def from_serial(self, state:dict) -> Self:
        """
        Deserialise a control.
        """
        name = state['control'][0].upper() + \
                state['control'][1:].lower()

        if not hasattr(yex.control, name):
            raise KeyError(state['control'])

        result = getattr(yex.control, name)()

        if 'value' in state:
            result.value = state['value']

        return result

    @classmethod
    def get_arguments_from_tokens(cls,
                                  types: List[Union[
                                      Tuple[str, Type],
                                      str,
                                      ]],
                                  tokens: 'yex.parse.Expander',
                                  ) -> List[Any]:
        """
        Finds arguments for a function, given a list of its
        parameters. This is a helper function for
        [the `@control` decorator](yex.decorator.control.md).

        Each entry in the list of parameters is either a
        bare string, giving the name of the parameter,
        or a (string, type) pair, giving the name and
        type annotation of the parameter. The result will
        be a list of values found for each parameter,
        in the same order.

        # How we find the values

        In this section, all mentions of yex's own types
        include their subclasses. For example, if we
        mention a Control, it includes all the subclasses of Control.

        ## If an entry has a type annotation

        ...

        ## If an entry doesn't have a type annotation

        ...

        # If an entry's name ends with `"all_args"`

        ...

        Raises:
            NeededSomethingElseError: if the token stream
                can't be construed to fit the parameters
            WeirdControlNameError: if there is no type
                annotation, and the name doesn't suggest
                what to look for
            WeirdControlAnnotationError: if the annotation
                is not a type we know how to produce
        """

        result = []

        ALL_ARGS_SUFFIX = 'all_args'

        if tokens is None:
            raise yex.exception.TokensWasNoneError()

        t = tokens.another(
                level = 'reading',
                on_eof = 'raise',
                )

        logger.debug('args: Looking for these arguments: %s', types)
        logger.debug('args: from this Expander: %s', tokens)

        for arg in types:

            if isinstance(arg, tuple):
                the_name, the_type = arg
                logger.debug('args: finding arg "%s", annotated as %s',
                        the_name, the_type)

                if isinstance(the_type, str):
                    the_type = globals()[the_type]
            else:
                the_name = arg
                the_type = None
                logger.debug('args: finding arg "%s", with no annotation',
                        the_name)

            if the_name.endswith(ALL_ARGS_SUFFIX) and the_type in [None, 'str']:
                value = ''

                level = the_name[:-len(ALL_ARGS_SUFFIX)-1]
                logger.debug('args: slurping up tokens at level "%s"',
                        level)

                for t in tokens.another(
                        level=level,
                        bounded='single',
                        on_eof='exhaust',
                        ):
                    value += str(t)

                logger.debug('args: which gives us: %s',
                        value)

            elif the_name=='tokens' and (
                    the_type is None or issubclass(the_type, yex.parse.Expander)
                    ):
                value = tokens

            elif the_name=='doc' and the_type in {None,
                                                  yex.document.Document}:
                value = tokens.doc

            elif the_name=='optional_equals' and the_type in {None, str}:
                value = tokens.eat_optional_char('=')

            elif the_type is None:
                logger.debug(
                           "args: can't work that out with no annotation")

                raise yex.exception.WeirdControlNameError(
                        argname = the_name,
                        )

            elif issubclass(the_type, int):
                logger.debug('args: looking for an integer')

                value = int(yex.value.Number.from_tokens(t))

            elif issubclass(the_type, yex.parse.Location):
                value = t.location

            elif issubclass(the_type, (
                    yex.parse.Token,
                    yex.control.Control,
                    )):

                logger.debug('args: looking for a %s in its own right',
                        the_type.__name__)

                # These might be in the token stream,
                # in their own right.

                value = t.next()

                if not isinstance(value, the_type):
                    logger.debug('args:   -- but we found a %s',
                            value.__class__.__name__)

                    raise yex.exception.NeededSomethingElseError(
                            needed = the_type,
                            problem = value,
                            )

            elif issubclass(the_type, (
                    yex.value.Value,
                    yex.box.Gismo,
                    yex.filename.Filename,
                    )):

                # These can be constructed from the token stream.

                logger.debug('args: constructing a %s',
                        the_type.__name__)

                value = the_type.from_tokens(t)

            else:
                logger.debug(
                        "args: can't work out an annotation of %s",
                        the_type.__name__)

                raise yex.exception.WeirdControlAnnotationError(
                        arg = the_name,
                        control = None,
                        annotation = the_type,
                        )

            logger.debug("args:  -- so %s == %s", the_name, value)
            result.append(value)

        logger.debug("args: result: %s", result)
        return result

class Expandable(Control):
    """
    These are procedures which create more tokens when they are run.

    Expandable controls include all macros, and
    some control flow primitives.

    TeXbook:
        211-212
    """
    def __call__(self, tokens: 'yex.parse.Expander'):
        logger.warning("%s: not implemented; you REALLY need to fix that",
                self)
        raise NotImplementedError()

    def __getstate__(self):
        return {
                'control': self.name,
                }

class Unexpandable(Control):
    """
    These are the most basic primitives, which carry out some
    kind of action when they are called.

    ## The mode flags

    There are three flags saying which modes an Unexpandable control
    run in. True means the control is permitted;
    False means it's forbidden; a string which is the name of a mode
    forces a switch to that mode before it's used.

    TeXbook:
        211-212
    """

    vertical: Union[bool, str] = True
    """Whether this control can run in vertical mode.
    See the class docstring for details."""

    horizontal: Union[bool, str] = True
    """Whether this control can run in horizontal mode.
    See the class docstring for details."""

    math: Union[bool, str] = True
    """Whether this control can run in math mode.
    See the class docstring for details."""

    def __call__(self, tokens: 'yex.parse.Expander'):
        logger.warning("%s: not implemented; you need to fix that",
                self)
        raise NotImplementedError()

    def __getstate__(self):
        result = {
                'control': self.name,
                }

        # There is no need to return the modes:
        # they're derivable from the name of the control.

        return result

    def query(self,
              tokens: 'yex.parse.Expander') -> Any:
        """
        Queries this control. See the class's docstring
        for more information.

        In the superclass, we simply return `self.value`.

        Some of our subclasses replace this using the
        `on_query` method in a decorated control.
        See [the @control decorator](yex.decorator.control.md)
        to find out more.
        """

        return self.value
