import logging
import inspect
import functools

logger = logging.getLogger('yex.general')

def control(
        **kwargs,
    ):
    r"""
    Decorator to turn a function into a C_Control object.

    When the result is activated (by calling it), we will call the
    wrapped function. The name and docstring of the result will be
    the same as those of the function.

    The result can be made queryable using its "on_query" method;
    see the docstring for that method for details.

    The args for the wrapped function act differently based on their
    names and their annotations. C_Control.get_arguments_from_tokens()
    has the canonical explanation of this, but here's an overview.
    The parameters are evaluated in order from left to right.

    If there's no type annotation, the name of the parameter could be:
        tokens: this receives the Expander.
        doc: this receives the Document.
        optional_equals: this consumes "=" if it's the next symbol,
            and receives it; if it's not the next symbol, it receives
            the empty string.
        reading_all_args, querying_all_args, executing_all_args: if
            the next symbol begins a group, these receive the concatenation
            of the string values of all symbols in that group. Otherwise,
            they receive the string value of the next symbol. The
            tokens are parsed at the level named in the parameter name.

    Any other name raises WeirdControlNameError.

    However, if the parameter is annotated with a type, the behaviour
    depends on what that type is:
        Value (including Number and Dimen), Filename, Gismo: the
            relevant symbol is constructed from the input stream.
        int: as if Number had been specified, except that the result
            is immediately cast to an int.
        Token (or any subclass), C_Control (or any subclass): receives
            the next symbol, which must belong to the class specified.
        Location: receives the current location. Nothing is consumed.

    Otherwise, we raise WeirdControlNameError.

    All args for the decorator itself are set directly on the result.
    Some of them also have other effects.
        vertical, horizontal, math: True if the control can be run in
            this mode; False if it can't; otherwise, running this control
            in the given mode will cause a mode switch, and this is a str
            naming the mode to switch to
        conditional (bool): if True, this control affects control flow
        expandable (bool): if True, the result will descend from C_Expandable;
            if False, which is the default, it will descend from
            C_Unexpandable.
        push_result (bool): if True, which is the default, the result
            of the wrapped function will be pushed back, and the call
            to the control will return None; if False, no push will
            be made and the call will return whatever the wrapped function
            returned.
        even_if_not_expanding (bool): if True, this control will be run
            even if we're currently not running controls in general--
            for example, straight after we've seen "\iffalse".
            Use with care.
    """

    PARAMS = {
            'vertical': True,
            'horizontal': True,
            'math': True,
            'expandable': False,
            'even_if_not_expanding': False,
            'push_result': True,
            'conditional': False,
            }

    for k in kwargs.keys():
        if k not in PARAMS:
            raise ValueError(
                    f"yex.decorator.control has no {k} param")

    def _control(fn):
        r"""
        Transformer from function to wrapped control.

        See the docstring of the parent class for why and how.

        Args:
            fn (function): a function

        Returns:
            a C_Control wrapping that function.
        """

        from yex.control.control import C_Expandable, C_Unexpandable

        def native_to_yex(item):
            r"""
            Turns ints and floats into Numbers.

            Passes everything else through unchanged.
            """
            import yex.value

            if isinstance(item, (int, float)):
                return yex.value.Number(item)
            else:
                return item

        if kwargs.get('expandable', False):
            parent_class = C_Expandable
        else:
            parent_class = C_Unexpandable

        argspec = inspect.getfullargspec(fn)
        class _Control(parent_class):
            """
            A control to wrap a function.
            """

            # attributes in PARAMS are set just after this class definition

            __doc__ = fn.__doc__

            def __init__(self, *fn_args, **fn_kwargs):
                super().__init__(*fn_args, **fn_kwargs)

            def __call__(self, tokens):

                fn_args = _argspec_to_fn_args(argspec, tokens,
                        self_object = None,
                        )

                received = fn(*fn_args)
                logger.debug("%s: result: %s", self, received)

                if received is None:
                    pass

                elif not kwargs.get('push_result', True):
                    logger.debug(
                            "%s:   -- push_result is False; returning that",
                            self)

                elif isinstance(received, list):
                    for item in reversed(received):
                        tokens.push(native_to_yex(item),
                                is_result=True,
                                )
                    return None

                else:
                    tokens.push(native_to_yex(received),
                            is_result=True,
                            )
                    return None

                return received

            @classmethod
            def on_query(cls):
                """
                Decorator to make a class of controls queryable.

                The decorated function becomes the query() function
                of the class, and is_queryable is set to True.

                The parameters of the wrapped function are interpreted
                in the same way as in the parent decorator.
                """

                import yex
                def _prep_control_object(fn):

                    argspec = inspect.getfullargspec(fn)

                    def do_query(self, tokens):
                        try:
                            fn_args = _argspec_to_fn_args(argspec, tokens,
                                    self_object = None,
                                    )
                        except yex.exception.ParseError as pe:
                            if self.is_queryable:
                                pe.mark_as_possible_rvalue(self)
                            raise

                        return fn(*fn_args)

                    cls.is_queryable = True
                    cls.query = do_query
                    return cls

                return _prep_control_object

            def __repr__(self):
                return '[\\'+fn.__name__.lower()+']'

        for f,v in PARAMS.items():
            setattr(_Control, f,
                    kwargs.get(f, v))
        _Control.__name__ = fn.__name__.title()

        return _Control

    return _control

##################

"""
def array():

    import yex

    def _array(fn):

        from yex.control.control import C_Unexpandable

        argspec = inspect.getfullargspec(fn)
        class _Array(C_Unexpandable):

            is_array = True
            __doc__ = fn.__doc__

            def __init__(self, *fn_args, **fn_kwargs):
                super().__init__(*fn_args, **fn_kwargs)

            def __call__(self, tokens):
                raise yex.exception.CalledAnArrayError()

            def get_member(self, *args, **kwargs):

                result = fn(*args, **kwargs)
                logger.debug("%s: result: %s", self, result)

                self._check_result(result)

                return result

            def get_member_from_tokens(self, tokens):

                fn_args = _argspec_to_fn_args(argspec, tokens,
                        self_object = None,
                        )

                result = fn(*fn_args)
                logger.debug("%s: result: %s", self, result)

                self._check_result(result)

                return result

            def _check_result(self, result):
                if not isinstance(result, yex.control.C_Unexpandable) or \
                        not result.is_queryable:
                            raise yex.exception.ArrayReturnWasWeirdError(
                                    problem = result,
                                    )

            def __repr__(self):
                return '[\\'+fn.__name__.lower()+']'

        _Array.__name__ = fn.__name__.title()
        _Array.__doc__ = fn.__doc__

        return _Array

    return _array
"""

##################

r"""
def get_member_from_tokens_method(
        **kwargs,
        ):
    def _get_member_from_tokens(fn):

        argspec = _check_first_element_is_self(inspect.getfullargspec(fn))

        def get_member_from_tokens(self, tokens):
            fn_args = _argspec_to_fn_args(argspec, tokens,
                    self_object = self,
                    )

            received = fn(*fn_args)
            logger.debug("%s: %s.get_member_from_tokens(%s) returns %s",
                self, fn, fn_args, received)
            return received

        return get_member_from_tokens

    return _get_member_from_tokens
    """

def _argspec_to_fn_args(argspec, tokens, self_object):
    r"""
    Parses a token stream according to a function's arguments.

    Args:
        argspec (inspect.FullArgSpec): the arguments to a function.
        tokens (Expander): a token stream.
        self_object (any or None): if this is None, it doesn't affect things.
            If it's not None, the first argument of argspec must be
            called "self", and it receives this value; this action
            consumes nothing.
    """

    import yex.control

    logger.debug("argspec %s", argspec)
    args = argspec.args

    if self_object is not None:
        _check_first_element_is_self(argspec)
        args = args[1:]
        logger.debug("args: %s (dropped 'self')", args)

    arg_types = []
    for arg in args:
        annotation = argspec.annotations.get(arg, None)

        arg_types.append( (arg, annotation) )

    logger.debug("arg_types: %s", arg_types)

    fn_args = yex.control.C_Control.get_arguments_from_tokens(
            types = arg_types,
            tokens = tokens,
            )

    if self_object is not None:
        fn_args.insert(0, self_object)

    return fn_args

def _check_first_element_is_self(a):
    """
    Checks that the first argument of "a" is named "self".

    If it isn't, raises ArgspecSelfError.
    """
    import yex.exception

    if not a.args:
        raise yex.exception.ArgspecSelfError()

    if a.args[0]!='self':
        raise yex.exception.ArgspecSelfError()

    return a
